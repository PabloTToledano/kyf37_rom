/*
	KYF37 keitai menu object ("keymenu") for the TWRP GUI engine.

	A cursor-less, D-pad driven list: one row is always highlighted, Up/Down move
	the highlight, OK (Enter) activates it, digit keys jump to/activate numbered
	rows, Left/Right page, * and # go to top/bottom.  Back/Clear is handled by the
	page (<action><touch key="355"/>...), except inside a directory browser where
	the menu consumes it to go up one directory.

	Modes (selected by child nodes of <keymenu>):
	  * static menu : <listitem name="..."> with <action> children (like <listbox>)
	  * browser     : <browse path=".." root=".." filter=".zip;.ZIP" pathvar="kb_path"
	                         filevar="tw_filename" selvar="tw_file" choosedirs="0|1"
	                         reverse="0|1"> + <action> children run when an entry is picked
	  * text viewer : <textfile path="/tmp/recovery.log" | pathvar=".." tail="400"
	                         wrap="44" start="end|top"/>

	Extra <listitem> attributes: value="%var%" (right aligned text), danger="1",
	hotkey="0".."9", shortcutonly="1" (OK refuses, only the digit works: used for
	the second confirmation step), member="/boot" listvar="tw_backup_list"
	(checkbox toggling an entry of a ';' separated list), availvar="var" (hide the row
	unless var contains member), and <data variable="x"/> (0/1 checkbox).

	This file is part of the KYF37 keitai recovery; license: GPLv3 like TWRP.
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <linux/input.h>

#include <algorithm>
#include <set>
#include <string>
#include <vector>

extern "C" {
#include "../twcommon.h"
}
#include "../minuitwrp/minui.h"

#include "rapidxml.hpp"
#include "objects.hpp"
#include "../data.hpp"
#include "../partitions.hpp"
#include "pages.hpp"
#include "placement.h"

extern std::vector<language_struct> Language_List;

namespace {
const int KEY_POUND_CODE = 253; // keitai '#'
std::string lower(std::string s) {
	for (size_t i = 0; i < s.size(); i++)
		if (s[i] >= 'A' && s[i] <= 'Z') s[i] += 32;
	return s;
}
bool ends_with_ci(const std::string& s, const std::string& suf) {
	if (suf.size() > s.size()) return false;
	return lower(s.substr(s.size() - suf.size())) == lower(suf);
}
std::string human_size(off_t n) {
	char b[32];
	if (n >= (off_t)1024 * 1024 * 1024) snprintf(b, sizeof(b), "%.1f GB", n / 1073741824.0);
	else if (n >= 1024 * 1024) snprintf(b, sizeof(b), "%.1f MB", n / 1048576.0);
	else if (n >= 1024) snprintf(b, sizeof(b), "%lld KB", (long long)(n / 1024));
	else snprintf(b, sizeof(b), "%lld B", (long long)n);
	return b;
}
std::string path_parent(const std::string& p) {
	if (p.size() <= 1) return "/";
	size_t e = p.size();
	while (e > 1 && p[e - 1] == '/') e--;
	size_t s = p.rfind('/', e - 1);
	if (s == std::string::npos || s == 0) return "/";
	return p.substr(0, s);
}
std::string path_join(const std::string& a, const std::string& b) {
	if (a.empty() || a == "/") return "/" + b;
	if (a[a.size() - 1] == '/') return a + b;
	return a + "/" + b;
}
struct KEnt { std::string name; bool dir; off_t size; };
struct KEntLess {
	bool rev;
	explicit KEntLess(bool r) : rev(r) {}
	bool operator()(const KEnt& a, const KEnt& b) const {
		if (a.dir != b.dir) return a.dir;
		int c = strcasecmp(a.name.c_str(), b.name.c_str());
		return rev ? c > 0 : c < 0;
	}
};
int digit_for_key(int key) { // KEY_1..KEY_9 = 2..10, KEY_0 = 11
	if (key >= KEY_1 && key <= KEY_9) return key - KEY_1 + 1;
	if (key == KEY_0) return 0;
	return -1;
}
}

GUIKeyMenu::GUIKeyMenu(xml_node<>* node) : GUIListBox(node)
{
	mFocus = 0;
	mMode = KM_STATIC;
	mNumbered = true;
	mKeepFocus = true;
	mStartFocus = 0;
	mBrowseAction = NULL;
	mChooseDirs = false;
	mReverse = false;
	mTail = 400;
	mWrap = 44;
	mStartEnd = false;
	mShowFocusBar = true;
	mLoadedPath = "";
	mPathVar = "kb_path";
	mFileVar = "tw_filename";
	mSelVar = "tw_file";
	mFilter = "";

	xml_attribute<>* attr = node->first_attribute("numbered");
	if (attr) mNumbered = atoi(attr->value()) != 0;
	mPaging = true;
	mShowSize = true;
	attr = node->first_attribute("paging");
	if (attr) mPaging = atoi(attr->value()) != 0;
	attr = node->first_attribute("keepfocus");
	if (attr) mKeepFocus = atoi(attr->value()) != 0;
	attr = node->first_attribute("startfocus");
	if (attr) mStartFocus = atoi(attr->value());

	// Per item extras: walk <listitem> children in the same order GUIListBox did.
	xml_node<>* child = node->first_node("listitem");
	size_t idx = 0;
	while (child && idx < mListItems.size()) {
		KMeta m;
		m.danger = false;
		m.shortcutOnly = false;
		m.hotkey = -1;
		xml_attribute<>* a = child->first_attribute("value");
		if (a) m.right = a->value();
		a = child->first_attribute("danger");
		if (a) m.danger = atoi(a->value()) != 0;
		a = child->first_attribute("shortcutonly");
		if (a) m.shortcutOnly = atoi(a->value()) != 0;
		a = child->first_attribute("hotkey");
		if (a) m.hotkey = atoi(a->value());
		a = child->first_attribute("member");
		if (a) m.member = a->value();
		a = child->first_attribute("listvar");
		if (a) m.listvar = a->value();
		a = child->first_attribute("availvar");
		if (a) m.availvar = a->value();
		a = child->first_attribute("mountpt");
		if (a) m.mountpt = a->value();
		mMeta.push_back(m);
		child = child->next_sibling("listitem");
		idx++;
	}
	mMeta.resize(mListItems.size());

	xml_node<>* b = node->first_node("browse");
	if (b) {
		mMode = KM_BROWSE;
		mBrowsePath = LoadAttrString(b, "path", "/");
		mBrowseRoot = LoadAttrString(b, "root", mBrowsePath.c_str());
		mFilter = LoadAttrString(b, "filter", "");
		mPathVar = LoadAttrString(b, "pathvar", "kb_path");
		mFileVar = LoadAttrString(b, "filevar", "tw_filename");
		mSelVar = LoadAttrString(b, "selvar", "tw_file");
		mRootVar = LoadAttrString(b, "rootvar", "");
		mShowSize = LoadAttrInt(b, "showsize", 1) != 0;
		mChooseDirs = LoadAttrInt(b, "choosedirs", 0) != 0;
		mReverse = LoadAttrInt(b, "reverse", 0) != 0;
		if (b->first_node("action") || b->first_node("actions"))
			mBrowseAction = new GUIAction(b);
		mNumbered = false;
	}
	xml_node<>* t = node->first_node("textfile");
	if (t) {
		mMode = KM_TEXT;
		mTextPath = LoadAttrString(t, "path", "");
		mPathVar = LoadAttrString(t, "pathvar", "");
		mTail = LoadAttrInt(t, "tail", 400);
		mWrap = LoadAttrInt(t, "wrap", 44);
		mStartEnd = LoadAttrString(t, "start", "end") == "end";
		mNumbered = false;
	}
	RebuildVisible("");
}

GUIKeyMenu::~GUIKeyMenu()
{
	delete mBrowseAction;
}

// ---- visibility / numbering -------------------------------------------------

bool GUIKeyMenu::ItemAvailable(size_t i)
{
	if (i >= mMeta.size()) return true;
	const KMeta& m = mMeta[i];
	if (m.availvar.empty() || m.member.empty()) return true;
	std::string v;
	DataManager::GetValue(m.availvar, v);
	return v.find(m.member + ";") != std::string::npos;
}

bool GUIKeyMenu::ItemChecked(size_t i)
{
	const KMeta& m = mMeta[i];
	if (!m.mountpt.empty())
		return PartitionManager.Is_Mounted_By_Path(m.mountpt);
	if (!m.member.empty() && !m.listvar.empty()) {
		std::string v;
		DataManager::GetValue(m.listvar, v);
		return v.find(m.member + ";") != std::string::npos;
	}
	if (!mListItems[i].variableName.empty())
		return DataManager::GetIntValue(mListItems[i].variableName) != 0;
	return false;
}

bool GUIKeyMenu::ItemIsCheck(size_t i)
{
	const KMeta& m = mMeta[i];
	return !m.mountpt.empty() || (!m.member.empty() && !m.listvar.empty()) || !mListItems[i].variableName.empty();
}

void GUIKeyMenu::RebuildVisible(const std::string& varName)
{
	if (mMode == KM_STATIC) {
		mVisibleItems.clear();
		for (size_t i = 0; i < mListItems.size(); i++) {
			bool vis = UpdateConditions(mListItems[i].mConditions, varName) && ItemAvailable(i);
			if (vis) mVisibleItems.push_back(i);
		}
	} else {
		mVisibleItems.clear();
		for (size_t i = 0; i < mListItems.size(); i++)
			mVisibleItems.push_back(i);
	}
	// numbering for shortcuts: explicit hotkeys first, rest sequential
	mNumberOf.assign(mVisibleItems.size(), -1);
	if (mNumbered) {
		std::set<int> used;
		for (size_t v = 0; v < mVisibleItems.size(); v++) {
			int hk = mMeta[mVisibleItems[v]].hotkey;
			if (hk >= 0 && hk <= 9) { mNumberOf[v] = hk; used.insert(hk); }
		}
		int next = 1;
		for (size_t v = 0; v < mVisibleItems.size(); v++) {
			if (mNumberOf[v] >= 0) continue;
			while (next <= 9 && used.count(next)) next++;
			if (next <= 9) { mNumberOf[v] = next; used.insert(next); next++; }
			else if (!used.count(0)) { mNumberOf[v] = 0; used.insert(0); }
		}
	}
	if (mFocus >= mVisibleItems.size())
		mFocus = mVisibleItems.empty() ? 0 : mVisibleItems.size() - 1;
	mUpdate = 1;
}

// ---- directory browser ------------------------------------------------------

void GUIKeyMenu::LoadDirectory()
{
	std::string path;
	if (!mRootVar.empty()) {
		std::string r = DataManager::GetStrValue(mRootVar);
		if (!r.empty()) mBrowseRoot = r;
	}
	DataManager::GetValue(mPathVar, path);
	if (path.empty()) path = mBrowsePath;
	struct stat st;
	if (stat(path.c_str(), &st) != 0 || !S_ISDIR(st.st_mode)) {
		path = mBrowseRoot;
		if (stat(path.c_str(), &st) != 0 || !S_ISDIR(st.st_mode)) path = "/";
	}
	while (path.size() > 1 && path[path.size() - 1] == '/') path.erase(path.size() - 1);
	if (path != mLoadedPath) mFocus = 0;
	mLoadedPath = path;
	if (DataManager::GetStrValue(mPathVar) != path)
		DataManager::SetValue(mPathVar, path);

	mListItems.clear();
	mMeta.clear();
	mBrowseIsDir.clear();
	std::vector<std::string> filters;
	{
		size_t s = 0;
		while (s < mFilter.size()) {
			size_t e = mFilter.find(';', s);
			if (e == std::string::npos) e = mFilter.size();
			if (e > s) filters.push_back(mFilter.substr(s, e - s));
			s = e + 1;
		}
	}
	std::vector<KEnt> ents;
	DIR* d = opendir(path.c_str());
	if (d) {
		struct dirent* de;
		while ((de = readdir(d)) != NULL) {
			if (!strcmp(de->d_name, ".") || !strcmp(de->d_name, "..")) continue;
			std::string full = path_join(path, de->d_name);
			struct stat fs;
			if (stat(full.c_str(), &fs) != 0) continue;
			KEnt e;
			e.name = de->d_name;
			e.dir = S_ISDIR(fs.st_mode);
			e.size = fs.st_size;
			if (!e.dir && !filters.empty()) {
				bool ok = false;
				for (size_t i = 0; i < filters.size(); i++)
					if (ends_with_ci(e.name, filters[i])) { ok = true; break; }
				if (!ok) continue;
			}
			ents.push_back(e);
		}
		closedir(d);
	}
	std::sort(ents.begin(), ents.end(), KEntLess(mReverse));
	if (path != mBrowseRoot && path != "/") {
		ListItem li;
		li.displayName = "..  (up)";
		li.selected = 0;
		li.action = NULL;
		li.variableValue = "..";
		mListItems.push_back(li);
		mMeta.push_back(KMeta());
		mMeta.back().danger = false; mMeta.back().shortcutOnly = false; mMeta.back().hotkey = -1;
	}
	for (size_t i = 0; i < ents.size(); i++) {
		ListItem li;
		li.displayName = ents[i].dir ? ents[i].name + "/" : ents[i].name;
		li.selected = 0;
		li.action = NULL;
		li.variableValue = ents[i].name;
		mListItems.push_back(li);
		KMeta m;
		m.danger = false; m.shortcutOnly = false; m.hotkey = -1;
		if (!ents[i].dir && mShowSize) m.right = human_size(ents[i].size);
		mMeta.push_back(m);
		mBrowseIsDir.resize(mListItems.size());
		mBrowseIsDir[mListItems.size() - 1] = ents[i].dir;
	}
	mBrowseIsDir.resize(mListItems.size());
	// ".." entry is not a dir flagged entry; handled by variableValue
	DataManager::SetValue("kb_empty", mListItems.empty() ? 1 : 0);
	RebuildVisible("");
	if (mFocus >= mVisibleItems.size()) mFocus = 0;
	SetVisibleListLocation(mFocus);
}

bool GUIKeyMenu::BrowseUp()
{
	if (mMode != KM_BROWSE) return false;
	if (mLoadedPath == mBrowseRoot || mLoadedPath == "/") return false;
	std::string old = mLoadedPath;
	std::string parent = path_parent(mLoadedPath);
	DataManager::SetValue(mPathVar, parent);
	LoadDirectory();
	// put focus on the directory we came from
	std::string base = old.substr(old.rfind('/') + 1);
	for (size_t v = 0; v < mVisibleItems.size(); v++)
		if (mListItems[mVisibleItems[v]].variableValue == base) { mFocus = v; break; }
	SetVisibleListLocation(mFocus);
	return true;
}

// ---- text viewer ------------------------------------------------------------

void GUIKeyMenu::LoadText()
{
	std::string path = mTextPath;
	if (!mPathVar.empty()) path = DataManager::GetStrValue(mPathVar);
	mListItems.clear();
	mMeta.clear();
	std::vector<std::string> lines;
	FILE* f = path.empty() ? NULL : fopen(path.c_str(), "r");
	if (!f) {
		lines.push_back("(cannot open " + path + ")");
	} else {
		fseek(f, 0, SEEK_END);
		long sz = ftell(f);
		long start = sz > 262144 ? sz - 262144 : 0;
		fseek(f, start, SEEK_SET);
		std::string cur;
		int c;
		while ((c = fgetc(f)) != EOF) {
			if (c == '\n') { lines.push_back(cur); cur.clear(); }
			else if (c == '\r') {}
			else if (c == '\t') cur += "    ";
			else if (c < 32 || c > 126) cur += '.';
			else cur += (char)c;
		}
		if (!cur.empty()) lines.push_back(cur);
		fclose(f);
		if (start > 0 && !lines.empty()) lines.erase(lines.begin());
	}
	std::vector<std::string> wrapped;
	size_t w = mWrap > 8 ? mWrap : 44;
	for (size_t i = 0; i < lines.size(); i++) {
		const std::string& l = lines[i];
		if (l.size() <= w) { wrapped.push_back(l); continue; }
		for (size_t p = 0; p < l.size(); p += w)
			wrapped.push_back((p ? "  " : "") + l.substr(p, w));
	}
	if ((int)wrapped.size() > mTail && mTail > 0)
		wrapped.erase(wrapped.begin(), wrapped.end() - mTail);
	if (wrapped.empty()) wrapped.push_back("(empty)");
	for (size_t i = 0; i < wrapped.size(); i++) {
		ListItem li;
		li.displayName = wrapped[i];
		li.selected = 0;
		li.action = NULL;
		mListItems.push_back(li);
		KMeta m;
		m.danger = false; m.shortcutOnly = false; m.hotkey = -1;
		mMeta.push_back(m);
	}
	RebuildVisible("");
	mFocus = mStartEnd ? (mVisibleItems.empty() ? 0 : mVisibleItems.size() - 1) : 0;
	firstDisplayedItem = 0;
	y_offset = 0;
	SetVisibleListLocation(mFocus);
}

// ---- GUI plumbing -----------------------------------------------------------

void GUIKeyMenu::SetPageFocus(int inFocus)
{
	GUIScrollList::SetPageFocus(inFocus);
	if (!inFocus) return;
	mDown.clear();
	if (!isTextParsed) {
		isTextParsed = true;
		for (size_t i = 0; i < mListItems.size(); i++)
			mListItems[i].displayName = gui_parse_text(mListItems[i].displayName);
	}
	if (mMode == KM_BROWSE) {
		LoadDirectory();
	} else if (mMode == KM_TEXT) {
		LoadText();
	} else {
		RebuildVisible("");
		if (!mKeepFocus) {
			mFocus = mStartFocus;
			firstDisplayedItem = 0;
			y_offset = 0;
		}
		if (mFocus >= mVisibleItems.size()) mFocus = 0;
		// never start on a "type the digit" row
		for (size_t n = 0; !mVisibleItems.empty() && n < mVisibleItems.size() && mMeta[mVisibleItems[mFocus]].shortcutOnly; n++)
			mFocus = (mFocus + 1) % mVisibleItems.size();
		SetVisibleListLocation(mFocus);
	}
	mUpdate = 1;
}

int GUIKeyMenu::NotifyVarChange(const std::string& varName, const std::string& value)
{
	GUIScrollList::NotifyVarChange(varName, value);
	if (!isConditionTrue()) return 0;
	if (mMode == KM_STATIC) {
		size_t before = mVisibleItems.size();
		RebuildVisible(varName);
		(void)before;
	} else if (mMode == KM_BROWSE && varName == mPathVar && value != mLoadedPath) {
		LoadDirectory();
	}
	mUpdate = 1;
	return 0;
}

int GUIKeyMenu::NotifyTouch(TOUCH_STATE state __unused, int x __unused, int y __unused)
{
	return 1; // no touch screen: ignore
}

size_t GUIKeyMenu::GetItemCount()
{
	return mVisibleItems.size();
}

void GUIKeyMenu::MoveFocus(int delta)
{
	size_t n = mVisibleItems.size();
	if (!n) return;
	size_t f = mFocus;
	for (size_t tries = 0; tries < n; tries++) {
		if (delta > 0) f = (f + 1) % n; else f = (f + n - 1) % n;
		if (mMode != KM_STATIC || !mMeta[mVisibleItems[f]].shortcutOnly) break;
	}
	if (mMode == KM_TEXT) { // text viewer: no wrap
		long nf = (long)mFocus + delta;
		if (nf < 0) nf = 0;
		if (nf >= (long)n) nf = n - 1;
		f = nf;
	}
	mFocus = f;
	SetVisibleListLocation(mFocus);
	mUpdate = 1;
}

void GUIKeyMenu::JumpFocus(long to)
{
	size_t n = mVisibleItems.size();
	if (!n) return;
	if (to < 0) to = 0;
	if (to >= (long)n) to = n - 1;
	mFocus = to;
	SetVisibleListLocation(mFocus);
	mUpdate = 1;
}

int GUIKeyMenu::NotifyKey(int key, bool down)
{
	if (!isConditionTrue()) return 1;
	int digit = digit_for_key(key);
	bool arrows = (key == KEY_UP || key == KEY_DOWN || key == KEY_LEFT || key == KEY_RIGHT);

	if (down) {
		if (arrows && !mPaging && (key == KEY_LEFT || key == KEY_RIGHT)) return 1;
		if (arrows) {
			int page = GetDisplayItemCount();
			if (page < 1) page = 1;
			if (key == KEY_UP) MoveFocus(-1);
			else if (key == KEY_DOWN) MoveFocus(1);
			else if (key == KEY_LEFT) JumpFocus((long)mFocus - page);
			else JumpFocus((long)mFocus + page);
			return 0; // consumed; lets the engine auto-repeat
		}
		if (key == KEY_KPASTERISK) { JumpFocus(0); return 0; }
		if (key == KEY_POUND_CODE) { JumpFocus((long)mVisibleItems.size() - 1); return 0; }
		if (key == KEY_ENTER || key == KEY_KPENTER || key == KEY_OK || key == KEY_SELECT || digit >= 0) {
			mDown.insert(key); // act on release, only if the press began on this page
			return 1;
		}
		if (key == KEY_BACK && mMode == KM_BROWSE) return BrowseUp() ? 0 : 1;
		return 1;
	}

	// release
	if (!mDown.erase(key)) return 1;
	if (key == KEY_BACK) return 1;
	if (mMode == KM_TEXT) return 1;
	if (digit >= 0) {
		for (size_t v = 0; v < mVisibleItems.size(); v++) {
			if (mNumberOf.size() > v && mNumberOf[v] == digit) {
				mFocus = v;
				SetVisibleListLocation(mFocus);
				Activate(v, true);
				return 0;
			}
		}
		return 1;
	}
	if (!mVisibleItems.empty()) {
		Activate(mFocus, false);
		return 0;
	}
	return 1;
}

void GUIKeyMenu::Activate(size_t v, bool viaShortcut)
{
	if (v >= mVisibleItems.size()) return;
	size_t ii = mVisibleItems[v];
	ListItem& it = mListItems[ii];
	mUpdate = 1;

	if (mMode == KM_BROWSE) {
		if (it.variableValue == "..") { BrowseUp(); return; }
		bool isdir = ii < mBrowseIsDir.size() && mBrowseIsDir[ii];
		std::string full = path_join(mLoadedPath, it.variableValue);
		if (isdir && !mChooseDirs) {
			DataManager::SetValue(mPathVar, full);
			LoadDirectory();
			return;
		}
		DataManager::SetValue(mSelVar, it.variableValue);
		DataManager::SetValue(mFileVar, full);
		if (mBrowseAction) mBrowseAction->doActions();
		return;
	}
	KMeta& m = mMeta[ii];
	if (m.shortcutOnly && !viaShortcut) {
		DataManager::SetValue("kb_hint", "Press the number key shown to confirm");
		return;
	}
	if (!m.mountpt.empty()) {
		if (PartitionManager.Is_Mounted_By_Path(m.mountpt))
			PartitionManager.UnMount_By_Path(m.mountpt, true);
		else
			PartitionManager.Mount_By_Path(m.mountpt, true);
	} else if (!m.member.empty() && !m.listvar.empty()) {
		std::string v2;
		DataManager::GetValue(m.listvar, v2);
		std::string tok = m.member + ";";
		size_t pos = v2.find(tok);
		if (pos == std::string::npos) v2 += tok; else v2.erase(pos, tok.size());
		DataManager::SetValue(m.listvar, v2);
	} else if (!it.variableName.empty()) {
		DataManager::SetValue(it.variableName, DataManager::GetIntValue(it.variableName) ? "0" : "1");
	}
	if (it.action) it.action->doActions();
}

// ---- rendering --------------------------------------------------------------

void GUIKeyMenu::RenderItem(size_t itemindex, int yPos, bool selected __unused)
{
	if (itemindex >= mVisibleItems.size()) return;
	size_t ii = mVisibleItems[itemindex];
	ListItem& it = mListItems[ii];
	KMeta& m = mMeta[ii];
	bool focus = (itemindex == mFocus);
	int h = actualItemHeight - mSeparatorH;
	void* font = mFont ? mFont->GetResource() : NULL;
	if (!font) return;
	int fh = mFontHeight;
	int ty = yPos + (h - fh) / 2;

	if (focus) {
		COLOR hc = hasHighlightColor ? mHighlightColor : mFontHighlightColor;
		gr_color(hc.red, hc.green, hc.blue, hc.alpha);
		gr_fill(mRenderX, yPos, mRenderW, h);
		if (mMode != KM_TEXT) { // accent marker on the left edge
			gr_color(mFontColor.red, mFontColor.green, mFontColor.blue, 255);
			gr_fill(mRenderX, yPos, 6, h);
		}
	}
	COLOR fc = focus ? mFontHighlightColor : mFontColor;
	if (m.danger && !focus) { fc.red = 255; fc.green = 96; fc.blue = 96; fc.alpha = 255; }
	if (m.shortcutOnly && !focus) { fc.red = 255; fc.green = 190; fc.blue = 60; fc.alpha = 255; }

	int x = mRenderX + 14;
	int rightEdge = mRenderX + mRenderW - 10 - (hasScroll ? mFastScrollW : 0);

	// number badge
	if (mNumbered && mNumberOf.size() > itemindex && mNumberOf[itemindex] >= 0) {
		char nb[4];
		snprintf(nb, sizeof(nb), "%d", mNumberOf[itemindex]);
		gr_color(fc.red, fc.green, fc.blue, focus ? 255 : 200);
		int bw = fh;
		gr_fill(x, yPos + 8, bw, h - 16); // solid badge, text drawn in inverse colour
		COLOR bg = focus ? mHighlightColor : mBackgroundColor;
		gr_color(bg.red, bg.green, bg.blue, 255);
		gr_textEx_scaleW(x + bw / 2, ty, nb, font, bw, CENTER_X_ONLY, 0);
		x += bw + 14;
	}
	// checkbox
	if (ItemIsCheck(ii)) {
		int bs = fh * 3 / 4;
		int by = yPos + (h - bs) / 2;
		gr_color(fc.red, fc.green, fc.blue, 255);
		gr_fill(x, by, bs, bs);
		COLOR bg = focus ? mHighlightColor : mBackgroundColor;
		gr_color(bg.red, bg.green, bg.blue, 255);
		gr_fill(x + 3, by + 3, bs - 6, bs - 6);
		if (ItemChecked(ii)) {
			gr_color(fc.red, fc.green, fc.blue, 255);
			gr_fill(x + 7, by + 7, bs - 14, bs - 14);
		}
		x += bs + 12;
	}
	// right-aligned value
	int rw = 0;
	if (!m.right.empty()) {
		std::string rt = gui_parse_text(m.right);
		if (!rt.empty()) {
			rw = gr_ttf_measureEx(rt.c_str(), font);
			int maxrw = (rightEdge - x) / 2;
			if (rw > maxrw) rw = maxrw;
			gr_color(fc.red, fc.green, fc.blue, focus ? 255 : 190);
			gr_textEx_scaleW(rightEdge, ty, rt.c_str(), font, rw, TOP_RIGHT, 1);
		}
	}
	gr_color(fc.red, fc.green, fc.blue, fc.alpha);
	int avail = rightEdge - x - (rw ? rw + 12 : 0);
	if (avail < 40) avail = 40;
	gr_textEx_scaleW(x, ty, it.displayName.c_str(), font, avail, TOP_LEFT, mMode == KM_TEXT ? 0 : 1);
}
