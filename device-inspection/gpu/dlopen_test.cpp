// usage: kyf37_dlopen_test <lib> [<lib>...]  - prints dlerror() for each, loading in order
#include <dlfcn.h>
#include <stdio.h>
int main(int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        void* h = dlopen(argv[i], RTLD_NOW);
        printf("%s -> %s%s\n", argv[i], h ? "OK" : "FAIL: ", h ? "" : dlerror());
    }
    return 0;
}
