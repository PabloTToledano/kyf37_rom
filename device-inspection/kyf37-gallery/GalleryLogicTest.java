package org.kyf37.gallery;

public final class GalleryLogicTest {
    static void check(boolean yes){if(!yes)throw new AssertionError();}
    static void rejects(String name){try{GalleryLogic.fileName(name);throw new AssertionError(name);}catch(IllegalArgumentException expected){}}
    public static void main(String[] args){
        for(String bad:new String[]{"",".","..","../photo","a/b","a\\b",".hidden","bad\nname","bad:name"})rejects(bad);
        check(GalleryLogic.fileName("  Holiday 2026.jpg ").equals("Holiday 2026.jpg"));
        check(GalleryLogic.fileName("旅の写真.jpg").equals("旅の写真.jpg"));
        check(GalleryLogic.albumPath("Trip").equals("Pictures/Trip/"));
        check(GalleryLogic.restoredPath("DCIM/Camera/",false).equals("DCIM/Camera/"));
        check(GalleryLogic.restoredPath("other/private",true).equals("Movies/"));
        try{GalleryLogic.restoredPath("Pictures/../Camera/",false);throw new AssertionError();}catch(IllegalArgumentException expected){}
        int[] crop=GalleryLogic.crop(101,53,-1,-1,2,2);check(crop[0]==0&&crop[1]==0&&crop[2]==101&&crop[3]==53);
        crop=GalleryLogic.crop(1,1,1,1,1,1);check(crop[2]-crop[0]==1&&crop[3]-crop[1]==1);
        crop=GalleryLogic.crop(320,480,.75f,.75f,.2f,.2f);check(crop[2]>crop[0]&&crop[3]>crop[1]);
        try{GalleryLogic.crop(10,10,Float.NaN,0,1,1);throw new AssertionError();}catch(IllegalArgumentException expected){}
        System.out.println("PASS: filename safety, restore paths, crop bounds and non-finite input");
    }
}
