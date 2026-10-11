# gpu agent E1: write a bad DMA_P_IBUF_ADDR for ~90us 12x mid-frame; 0 IOMMU faults => register is latched at frame start. Run as root on a static screen. Restores the original value.
cd /sys/kernel/debug/mdp
echo '90008 4' > off
ORIG=$(cat reg | head -1 | awk '{print $2}')
echo orig=$ORIG
T=/sys/kernel/debug/tracing
echo 0 > $T/tracing_on; echo > $T/trace
echo 1 > $T/tracing_on
i=0
while [ $i -lt 12 ]; do
 echo "90008 3f000000" > reg
 echo "90008 $ORIG" > reg
 usleep 37000
 i=$((i+1))
done
echo 0 > $T/tracing_on
grep -v '^#' $T/trace | cut -c1-150 | grep -E 'regw|FAR' 
dmesg | grep -c 'IOMMU page fault'
echo '90008 4' > off; cat reg | head -1
