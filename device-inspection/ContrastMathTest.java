package org.kyf37.home;

public final class ContrastMathTest {
    private static void expect(String name,int color,int background){
        double[] samples=new double[35];
        java.util.Arrays.fill(samples,ContrastMath.luminance(background));
        if(ContrastMath.colorFor(samples)!=color)throw new AssertionError(name);
    }
    public static void main(String[] args){
        expect("white wallpaper",ContrastMath.DARK,0xFFFFFFFF);
        expect("black wallpaper",ContrastMath.LIGHT,0xFF000000);
        expect("bright blue wallpaper",ContrastMath.DARK,0xFFBDEAFF);
        expect("dark blue wallpaper",ContrastMath.LIGHT,0xFF091128);
        double[] stars=new double[35];
        java.util.Arrays.fill(stars,0);
        for(int i=0;i<10;i++)stars[i]=1;
        if(ContrastMath.colorFor(stars)!=ContrastMath.LIGHT)throw new AssertionError("dark wallpaper with bright stars");
        for(int i=0;i<35;i++)stars[i]=1-stars[i];
        if(ContrastMath.colorFor(stars)!=ContrastMath.DARK)throw new AssertionError("bright wallpaper with dark patches");
        System.out.println("PASS: solid light/dark, blue light/dark, and mixed wallpaper contrast");
    }
}
