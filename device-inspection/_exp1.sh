/data/local/tmp/kyf37_diag2 70 - > /data/local/tmp/d.txt 2>&1 &
sleep 20
date +%s > /data/local/tmp/mark1
/data/local/tmp/kyf37_radio_ctl > /data/local/tmp/r.txt 2>&1
date +%s > /data/local/tmp/mark2
wait
