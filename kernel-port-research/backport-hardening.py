"""Re-runnable security/display changes in the independent kernel only.

1. Binder: remove the thread waitqueue from epoll before freeing the thread
   (CVE-2019-2215 "bad binder" use-after-free).
2. MDP3 video mode: program the DMA buffer address inside the vertical-blanking
   window right after start-of-frame instead of at an arbitrary scan position
   (physical-panel tearing). Runtime switch:
   /sys/module/mdss_mdp3/parameters/kyf37_vblank_sync (1 = on, 0 = original).
"""
from pathlib import Path

kernel = Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')
assert kernel.resolve() == Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')


def replace(path, old, new):
    p = kernel / path
    data = p.read_text()
    if new in data:
        return
    assert data.count(old) == 1, (path, old)
    p.write_text(data.replace(old, new, 1))


# ---- 1. binder ---------------------------------------------------------
B = 'drivers/staging/android/binder.c'
replace(B, '\tBINDER_LOOPER_STATE_NEED_RETURN = 0x20\n',
        '\tBINDER_LOOPER_STATE_NEED_RETURN = 0x20,\n'
        '\tBINDER_LOOPER_STATE_POLL        = 0x40\n')
replace(B, '\tbinder_release_work(&thread->todo);\n\tkfree(thread);\n',
        '''\tbinder_release_work(&thread->todo);
\t/*
\t * If this thread was ever polled, epoll may still hold its waitqueue.
\t * Detach it with POLLFREE and let RCU readers finish before freeing.
\t */
\tif (thread->looper & BINDER_LOOPER_STATE_POLL) {
\t\tif (waitqueue_active(&thread->wait))
\t\t\twake_up_poll(&thread->wait, POLLHUP | POLLFREE);
\t\tsynchronize_rcu();
\t}
\tkfree(thread);
''')
replace(B, '''\t\tpoll_wait(filp, &thread->wait, wait);
\t\tif (binder_has_thread_work(thread))
\t\t\treturn POLLIN;
''', '''\t\tthread->looper |= BINDER_LOOPER_STATE_POLL;
\t\tpoll_wait(filp, &thread->wait, wait);
\t\tif (binder_has_thread_work(thread))
\t\t\treturn POLLIN;
''')

# ---- 2. MDP3 vblank-synchronised address write -------------------------
D = 'drivers/video/msm/mdss/mdp3_dma.c'
replace(D, '#include "mdss_debug.h"\n\n',
        '''#include "mdss_debug.h"
#include <linux/ktime.h>
#include <linux/moduleparam.h>

/*
 * Video-mode panels scan the buffer continuously. Writing the address while
 * lines are being fetched can tear. Start-of-frame is followed by the sync
 * pulse and back porch (no active lines); program the address in that window.
 */
static bool kyf37_vblank_sync = true;
module_param(kyf37_vblank_sync, bool, 0644);
unsigned int kyf37_porch_us;
static ktime_t kyf37_last_sof;

''')
replace(D, '\tpr_debug("mdp3_vsync_intr_handler\\n");\n\tspin_lock(&dma->dma_lock);\n',
        '\tpr_debug("mdp3_vsync_intr_handler\\n");\n\tkyf37_last_sof = ktime_get();\n\tspin_lock(&dma->dma_lock);\n')
replace(D, '''\tmutex_lock(&dma->pp_lock);
\tif (dma->ccs_config.ccs_dirty)
\t\tmdp3_ccs_update(dma, true);
\tmutex_unlock(&dma->pp_lock);
\tspin_lock_irqsave(&dma->dma_lock, flag);
\tMDP3_REG_WRITE(MDP3_REG_DMA_P_IBUF_ADDR,''', '''\tmutex_lock(&dma->pp_lock);
\tif (dma->ccs_config.ccs_dirty)
\t\tmdp3_ccs_update(dma, true);
\tmutex_unlock(&dma->pp_lock);
\tif (kyf37_vblank_sync && kyf37_porch_us &&
\t\t\tdma->output_config.out_sel == MDP3_DMA_OUTPUT_SEL_DSI_VIDEO &&
\t\t\tintf->active &&
\t\t\tktime_us_delta(ktime_get(), kyf37_last_sof) >
\t\t\t\t(s64)kyf37_porch_us) {
\t\t/* Outside the blanking window: wait for the next frame start. */
\t\tspin_lock_irqsave(&dma->dma_lock, flag);
\t\tdma->vsync_status = MDP3_REG_READ(MDP3_REG_INTR_STATUS) &
\t\t\t(1 << MDP3_INTR_LCDC_START_OF_FRAME);
\t\tinit_completion(&dma->vsync_comp);
\t\tspin_unlock_irqrestore(&dma->dma_lock, flag);
\t\tmdp3_dma_callback_enable(dma, cb_type);
\t\t/* Timeout is tolerated: fall through to the original behaviour. */
\t\twait_for_completion_timeout(&dma->vsync_comp, KOFF_TIMEOUT);
\t}
\tspin_lock_irqsave(&dma->dma_lock, flag);
\tMDP3_REG_WRITE(MDP3_REG_DMA_P_IBUF_ADDR,''')

H = 'drivers/video/msm/mdss/mdp3_dma.h'
replace(H, 'int mdp3_dma_init(struct mdp3_dma *dma);\n',
        'extern unsigned int kyf37_porch_us;\n\nint mdp3_dma_init(struct mdp3_dma *dma);\n')

C = 'drivers/video/msm/mdss/mdp3_ctrl.c'
replace(C, '\tvsync_period *= hsync_period;\n\n\tcfg.type = mdp3_ctrl_get_intf_type(mfd);\n',
        '''\t{
\t\t/* 3/4 of sync pulse + back porch: safe window after frame start. */
\t\tu32 fps = mdss_panel_get_framerate(p);
\t\tu32 lines = vsync_period;
\t\tu32 porch = v_pulse_width + v_back_porch + border_top;

\t\tkyf37_porch_us = 0;
\t\tif (fps && lines && porch)
\t\t\tkyf37_porch_us = (u32)div_u64(
\t\t\t\t(u64)porch * 3000000ULL, 4ULL * fps * lines);
\t}
\tvsync_period *= hsync_period;

\tcfg.type = mdp3_ctrl_get_intf_type(mfd);
''')
print('hardening applied')
