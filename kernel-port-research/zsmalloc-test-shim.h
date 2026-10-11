/* ARM32 allocator test primitives. These do not model kernel concurrency. */
typedef unsigned int size_t;
typedef unsigned long gfp_t;
typedef unsigned long long u64;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void *)0)
#define PAGE_SHIFT 12
#define PAGE_SIZE (1UL << PAGE_SHIFT)
#define BITS_PER_LONG 32
#define GFP_KERNEL 0
#define __GFP_HIGHMEM 1
#define ENOMEM 12
#define EINVAL 22
#define ENODEV 19
#define likely(x) (x)
#define unlikely(x) (x)
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define DIV_ROUND_UP(n,d) (((n)+(d)-1)/(d))
#define ALIGN(n,a) (((n)+(a)-1)&~((a)-1))
#define BIT(n) (1UL<<(n))
#define _AC(x,t) x##t
#define ACCESS_ONCE(x) (*(volatile __typeof__(x) *)&(x))
#define __init
#define __exit
#define __read_mostly
#define uninitialized_var(x) x
#define EXPORT_SYMBOL_GPL(x)
#define module_init(x)
#define module_exit(x)
#define MODULE_LICENSE(x)
#define MODULE_AUTHOR(x)
#define pr_info(...) ((void)0)
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
static void trace(char c) {
    register long r0 __asm__("r0")=2;
    register const char *r1 __asm__("r1")=&c;
    register long r2 __asm__("r2")=1;
    register long r7 __asm__("r7")=4;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r1), "r"(r2), "r"(r7) : "memory");
}
static void stop(int code) {
    register long r0 __asm__("r0")=code;
    register long r7 __asm__("r7")=1;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r7) : "memory");
    for (;;) {}
}
#define BUG_ON(x) do { if (x) stop(99); } while (0)
#define VM_BUG_ON(x) BUG_ON(x)
static void *memcpy(void *d, const void *s, size_t n) {
    char *out=d; const char *in=s; size_t i;
    for (i=0;i<n;i++) out[i]=in[i]; return d;
}
static void *memset(void *d, int c, size_t n) {
    char *out=d; size_t i; for (i=0;i<n;i++) out[i]=c; return d;
}
static unsigned char heap[8388608] __attribute__((aligned(8)));
static unsigned int heap_used;
static int fail_allocation;
static void *kmalloc(size_t n, gfp_t flags) {
    void *out; (void)flags;
    if (fail_allocation) return NULL;
    n=ALIGN(n,8); BUG_ON(heap_used+n>sizeof(heap));
    out=heap+heap_used; heap_used+=n; return out;
}
static void *kzalloc(size_t n, gfp_t f) { void *p=kmalloc(n,f); if (p) memset(p,0,n); return p; }
static void *kcalloc(size_t n,size_t size,gfp_t f) { return kzalloc(n*size,f); }
static void kfree(void *p) { (void)p; }
static char *kstrdup(const char *s,gfp_t f) {
    size_t n=0; char *p; while(s[n]) n++; p=kmalloc(n+1,f); if(p) memcpy(p,s,n+1); return p;
}
struct kmem_cache { int unused; };
static struct kmem_cache *kmem_cache_create(const char *s,size_t n,size_t a,int f,void *ctor) {
    (void)s; (void)n; (void)a; (void)f; (void)ctor; return kzalloc(sizeof(struct kmem_cache),0);
}
static void kmem_cache_destroy(struct kmem_cache *p) { kfree(p); }
static void *kmem_cache_alloc(struct kmem_cache *p,gfp_t f) { (void)p; return kmalloc(sizeof(unsigned long),f); }
static void kmem_cache_free(struct kmem_cache *p,void *obj) { (void)p; kfree(obj); }
typedef int spinlock_t;
static int held_locks, mappings, preemptions, faults;
static void spin_lock_init(spinlock_t *p) { *p=0; }
static void spin_lock(spinlock_t *p) { BUG_ON(*p); *p=1; held_locks++; }
static void spin_unlock(spinlock_t *p) { BUG_ON(!*p); *p=0; held_locks--; }
static int test_and_set_bit_lock(int bit,unsigned long *p) { int old=!!(*p & BIT(bit)); *p|=BIT(bit); return old; }
static void clear_bit_unlock(int bit,unsigned long *p) { *p&=~BIT(bit); }
static void clear_bit(int bit,unsigned long *p) { *p&=~BIT(bit); }
typedef struct { long value; } atomic_long_t;
static long atomic_long_read(atomic_long_t *p) { return p->value; }
static void atomic_long_add(long n,atomic_long_t *p) { p->value+=n; }
static void atomic_long_sub(long n,atomic_long_t *p) { p->value-=n; }
struct list_head { struct list_head *next,*prev; };
#define INIT_LIST_HEAD(p) ((p)->next=(p)->prev=(p))
#define list_entry(p,t,m) ((t *)((char *)(p)-__builtin_offsetof(t,m)))
#define list_for_each_entry_safe(p,n,h,m) for(p=list_entry((h)->next,__typeof__(*p),m),n=list_entry(p->m.next,__typeof__(*p),m); &p->m!=(h);p=n,n=list_entry(n->m.next,__typeof__(*n),m))
static int list_empty(struct list_head *p) { return p->next==p; }
static void list_add(struct list_head *p,struct list_head *h) { p->next=h->next;p->prev=h;h->next->prev=p;h->next=p; }
static void list_add_tail(struct list_head *p,struct list_head *h) { list_add(p,h->prev); }
static void list_del(struct list_head *p) { p->prev->next=p->next;p->next->prev=p->prev; }
static void list_del_init(struct list_head *p) { list_del(p);INIT_LIST_HEAD(p); }
struct address_space;
struct page {
    unsigned long flags;
    union { struct page *first_page; unsigned long private; };
    union { unsigned long index; void *freelist; };
    struct list_head lru;
    unsigned int objects,inuse;
    struct address_space *mapping;
};
#define PG_private 0
#define PG_private_2 1
#define PagePrivate(p) (!!((p)->flags & 1))
#define PagePrivate2(p) (!!((p)->flags & 2))
#define SetPagePrivate(p) ((p)->flags|=1)
#define SetPagePrivate2(p) ((p)->flags|=2)
#define page_private(p) ((p)->private)
#define set_page_private(p,n) ((p)->private=(n))
#define page_mapcount_reset(p) ((void)0)
static struct page test_pages[1024];
static unsigned char test_data[1024][PAGE_SIZE] __attribute__((aligned(4096)));
static int page_used[1024], live_pages;
static unsigned long page_to_pfn(struct page *p) { return (p-test_pages)+1; }
static struct page *pfn_to_page(unsigned long n) { BUG_ON(n==0 || n>1024);return &test_pages[n-1]; }
static struct page *alloc_page(gfp_t f) {
    int i;(void)f;if(fail_allocation)return NULL;
    for(i=0;i<1024;i++) if(!page_used[i]) {
        page_used[i]=1;live_pages++;memset(&test_pages[i],0,sizeof(struct page));
        memset(test_data[i],0xcc,PAGE_SIZE);return &test_pages[i];
    }
    return NULL;
}
static void __free_page(struct page *p) { int i=p-test_pages;BUG_ON(!page_used[i]);page_used[i]=0;live_pages--; }
static void *kmap_atomic(struct page *p) { BUG_ON(!page_used[p-test_pages]);mappings++;return test_data[p-test_pages]; }
static void kunmap_atomic(void *p) { (void)p;BUG_ON(!mappings);mappings--; }
static void pagefault_disable(void) { faults++; }
static void pagefault_enable(void) { BUG_ON(!faults);faults--; }
static int in_interrupt(void) { return 0; }
static void cond_resched(void) { BUG_ON(held_locks || mappings || preemptions || faults); }
#define DEFINE_PER_CPU(t,n) t n
#define per_cpu(n,c) (n)
#define get_cpu_var(n) (preemptions++,(n))
#define put_cpu_var(n) do { BUG_ON(!preemptions);preemptions--; } while(0)
#undef get_cpu_var
/* GCC statement-expression yields an lvalue, matching the kernel macro. */
#define get_cpu_var(n) (*({preemptions++;&(n);}))
#define this_cpu_ptr(p) (p)
struct notifier_block { int (*notifier_call)(struct notifier_block *,unsigned long,void *); };
#define CPU_UP_PREPARE 1
#define CPU_DEAD 2
#define CPU_UP_CANCELED 3
#define NOTIFY_OK 0
#define notifier_from_errno(x) (x)
#define notifier_to_errno(x) (x)
#define cpu_notifier_register_begin() ((void)0)
#define cpu_notifier_register_done() ((void)0)
#define __register_cpu_notifier(p) ((void)0)
#define __unregister_cpu_notifier(p) ((void)0)
#define for_each_online_cpu(cpu) for(cpu=0;cpu<1;cpu++)
enum zs_mapmode { ZS_MM_RW,ZS_MM_RO,ZS_MM_WO };
struct zs_pool;
struct zs_pool *zs_create_pool(gfp_t);
void zs_destroy_pool(struct zs_pool *);
unsigned long zs_malloc(struct zs_pool *,size_t);
void zs_free(struct zs_pool *,unsigned long);
void *zs_map_object(struct zs_pool *,unsigned long,enum zs_mapmode);
void zs_unmap_object(struct zs_pool *,unsigned long);
unsigned long zs_get_total_pages(struct zs_pool *);
