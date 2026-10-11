package org.kyf37.gallery;

/** Pure rules shared by the UI, media operations and host regression checks. */
public final class GalleryLogic {
    private GalleryLogic() { }
    public static String fileName(String value) {
        String s = value == null ? "" : value.trim();
        if (s.isEmpty() || s.equals(".") || s.equals("..") || s.length() > 160
                || s.indexOf('/') >= 0 || s.indexOf('\\') >= 0 || s.startsWith("."))
            throw new IllegalArgumentException("Use a visible name without / or \\");
        for (int i = 0; i < s.length(); i++)
            if (Character.isISOControl(s.charAt(i)) || ":*?\"<>|".indexOf(s.charAt(i)) >= 0)
                throw new IllegalArgumentException("The name contains an unsupported character");
        return s;
    }
    public static String albumPath(String name) { return "Pictures/" + fileName(name) + "/"; }
    public static String restoredPath(String path, boolean video) {
        if (path == null || path.isEmpty()) return video ? "Movies/" : "Pictures/";
        String[] parts = path.split("/");
        if (parts.length == 0 || !(parts[0].equals("DCIM") || parts[0].equals("Pictures")
                || parts[0].equals("Movies") || parts[0].equals("Download")))
            return video ? "Movies/" : "Pictures/";
        for (String part : parts) if (!part.isEmpty()) fileName(part);
        return path.endsWith("/") ? path : path + "/";
    }
    /** Crop bounds in oriented source pixels, always nonempty and inside the image. */
    public static int[] crop(int width, int height, float left, float top, float right, float bottom) {
        if (width < 1 || height < 1) throw new IllegalArgumentException("Empty image");
        if (!Float.isFinite(left) || !Float.isFinite(top) || !Float.isFinite(right) || !Float.isFinite(bottom))
            throw new IllegalArgumentException("Invalid crop");
        int l = Math.max(0, Math.min(width - 1, (int)Math.floor(left * width)));
        int t = Math.max(0, Math.min(height - 1, (int)Math.floor(top * height)));
        int r = Math.max(l + 1, Math.min(width, (int)Math.ceil(right * width)));
        int b = Math.max(t + 1, Math.min(height, (int)Math.ceil(bottom * height)));
        return new int[] {l, t, r, b};
    }
    public static int sampleSide(int width, int height, int maxSide) {
        return Math.max(1, Math.round(Math.min(1f, (float)maxSide / Math.max(width, height)) * width));
    }
}
