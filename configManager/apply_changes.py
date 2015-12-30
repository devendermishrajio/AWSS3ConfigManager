from manager import ConfigManager
import sys
if __name__ == '__main__':
  if len( sys.argv) < 2:
    print "Config File path required"
    sys.exit(-1)
  file = sys.argv[2]
  configManager = ConfigManager(sys.argv[1])
  configManager.reportOrApplyConfigChange(file, apply_flag = True)
