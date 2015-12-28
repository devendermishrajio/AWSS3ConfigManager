import configReader 
import logging
import helper
import os
import difflib
import filecmp

logger = logging.getLogger("s3Integration")

class ConfigChangeDetector:
  
  '''
    detects changes in old and new config. Also creates diff files for new and old configs. 
  '''
  
  def __init__(self, oldConfig, newConfig):
    print "oldconfig ------", oldConfig
    print "newconfig ------", newConfig
    self.oldConfig = oldConfig
    self.newConfig = newConfig
    self.diff = "/tmp/config_diff.conf"
  
  def compareConfig(self):
    flag = filecmp.cmp(self.newConfig, self.oldConfig)
    if flag is True:
      return True
    fp = open(self.diff, "w")
    for line in difflib.unified_diff(open(self.oldConfig).readlines(), open(self.newConfig).readlines(), self.oldConfig, self.newConfig):
      fp.write(line)
    fp.close()
    return False

  def getDiffInOldConfig(self):
    return self.diff_old

  def getDiffInNewConfig(self):
    return self.diff_new
  
  def getDiff(self):
    return self.diff


class ConfigChangeApplier:
  
  '''
    applies config change to remote host by copying new config to the specified path on the given node.  
  '''

  def __init__(self, config, conf_dir, path):
    self.config = config
    print "**********", conf_dir
    self.path = path 
    try:
      helper.Helper.copyConfig(config, os.path.join(conf_dir, path)) 
    except Exception:
      logger.error("Unable to copy file " + config + " at location " + path)
      raise Exception("Unable to copy file " + config + " at location " + path)
