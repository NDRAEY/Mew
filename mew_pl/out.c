#include "/data/data/com.termux/files/home/Mew/mew_pl/targets/linux//defs.h"
#include "/data/data/com.termux/files/home/Mew/mew_pl/targets/linux//alloc.h"

typedef struct mystruct {
u32 a;
u32 b;
u16 c;
u8 d;

} mystruct;

mystruct* init_this() {

mystruct* a = __allocator_alloc(11);
mystruct* e = __allocator_alloc(11);
u32 c = 0;
c = (c + 1);
__allocator_free(e);
return a;
}

void main() {

mystruct* test = init_this();
printf("Hello!");
printf("\n");
__allocator_free(test);

}

