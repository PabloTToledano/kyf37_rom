// KYF37 keitai: cursor-less D-pad menu (see keymenu.cpp)
class GUIKeyMenu : public GUIListBox
{
public:
	GUIKeyMenu(xml_node<>* node);
	virtual ~GUIKeyMenu();

public:
	virtual void SetPageFocus(int inFocus);
	virtual int NotifyVarChange(const std::string& varName, const std::string& value);
	virtual int NotifyTouch(TOUCH_STATE state, int x, int y);
	virtual int NotifyKey(int key, bool down);
	virtual size_t GetItemCount();
	virtual void RenderItem(size_t itemindex, int yPos, bool selected);

protected:
	enum Mode { KM_STATIC, KM_BROWSE, KM_TEXT };
	struct KMeta {
		std::string right, member, listvar, availvar, mountpt;
		bool danger, shortcutOnly;
		int hotkey;
		KMeta() : danger(false), shortcutOnly(false), hotkey(-1) {}
	};
	std::vector<KMeta> mMeta;      // parallel to mListItems
	std::vector<int> mNumberOf;    // digit shown for each visible row (-1 none)
	std::vector<bool> mBrowseIsDir;
	std::set<int> mDown;
	size_t mFocus;
	Mode mMode;
	bool mShowSize, mPaging, mNumbered, mKeepFocus, mChooseDirs, mReverse, mStartEnd, mShowFocusBar;
	int mStartFocus, mTail, mWrap;
	GUIAction* mBrowseAction;
	std::string mBrowsePath, mBrowseRoot, mLoadedPath, mPathVar, mFileVar, mSelVar, mFilter, mTextPath, mRootVar;

	bool ItemAvailable(size_t i);
	bool ItemChecked(size_t i);
	bool ItemIsCheck(size_t i);
	void RebuildVisible(const std::string& varName);
	void LoadDirectory();
	bool BrowseUp();
	void LoadText();
	void MoveFocus(int delta);
	void JumpFocus(long to);
	void Activate(size_t visibleIndex, bool viaShortcut);
};

