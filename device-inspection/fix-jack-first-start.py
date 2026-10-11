from pathlib import Path

p = Path('/home/pablo/kyf37-lineage/prebuilts/sdk/tools/jack-admin')
s = p.read_text()
old = 'isServerRunning () {\n'
new = old + '''  # Certificates are created by the first server launch. Modern curl exits
  # with option error 2 for absent PEM files, rather than connection error 7.
  if [ ! -r "${JACK_HOME}/server.pem" ] || [ ! -r "${JACK_HOME}/client.pem" ]; then
    return 1
  fi
'''
if new not in s:
    assert s.count(old) == 1
    s = s.replace(old, new, 1)
old_wait = '''waitServerStarted () {
  DONE=1
  let DATE_TIMEOUT=$(date +%s)+$JACK_CONNECTION_TIMEOUT
  while [ "$DONE" -ne 0 ]; do
'''
new_wait = old_wait + '''    # Allow the newly launched JVM to export its mutual TLS certificates.
    if [ ! -r "${JACK_HOME}/server.pem" ] || [ ! -r "${JACK_HOME}/client.pem" ]; then
      if [ $(date +%s) -ge $DATE_TIMEOUT ]; then
        echo "Jack server did not create its certificates" >&2
        abort
      fi
      sleep 1
      continue
    fi
'''
if new_wait not in s:
    assert s.count(old_wait) == 1
    s = s.replace(old_wait, new_wait, 1)
p.write_text(s)
print('Jack first-start certificate check installed')
