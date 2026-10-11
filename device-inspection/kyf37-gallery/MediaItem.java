package org.kyf37.gallery;

import android.net.Uri;

final class MediaItem {
    Uri uri;
    String name = "", mime = "image/jpeg", album = "", path = "", volume = "external_primary";
    long date, modified, size, duration;
    int width, height;
    boolean video, trash, managed;
    String trashId;
    String key() { return uri.toString(); }
    String albumKey() { return volume + ":" + path; }
}
