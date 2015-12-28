import configChangeNotifier 
import mailServer
import s3Dao
import helper
import configReader
import logging, os

logger = logging.getLogger("s3Integration")
logger.addHandler(logging.FileHandler("/var/log/s3Integration.log"))

class ConfigManager:

  def __init__(self, config_file):
    self.SECTION = "Manager"
    self.CONF_DIR = "ConfDir"
    self.MAIL_SERVER = "mailServer"
    self.MAIL_SENDER = "mailSender"
    self.MAIL_PASSWORD = "mailPassword"
    self.MAIL_RECEIVER = "mailReceiver"
    self.HTTP_PROXY_ADDR = "http-proxy-addr"
    self.HTTP_PROXY_PORT = "http-proxy-port"
    self.MAIL_SUBJECT = "mailSubject"#"JCS_Config_Change_Notification"
    self.BUCKET = "s3Bucket"
    
    try:
      self.configReader = configReader.ConfigReader(config_file)#("/tmp/Config_Manager_config.conf")
      self.S3_BUCKET = self.configReader.getValue(self.SECTION, self.BUCKET) 
      self.conf_dir = self.configReader.getValue(self.SECTION, self.CONF_DIR)
      print "Bucket initialized with :", self.S3_BUCKET
    except Exception:
      print "Invalid config file"
      logger.error("Invalid config file")
    self.s3Dao = s3Dao.S3Dao()
    self.s3Dao.setBucket(self.S3_BUCKET)
    print "S3 Dao Initialized"

  def reportAllConfigChange(self):
    print "Inside reportAllConfigChange"
    objects = self.getAllS3Objects()
    print "S3 objects : ", objects
    for obj in objects:
      if not obj.endswith("/"):
        print "Processing Object : ", obj
        self.reportOrApplyConfigChange(obj)      

  def reportOrApplyConfigChange(self, objectKey, apply_flag = False):
    newConfig = os.path.join("/tmp/new" , objectKey)
    self.getS3Object(objectKey, newConfig)
    try:
      OLD_CONFIG_PATH = objectKey #self.getConfigPath(objectKey)
      OLD_CONFIG_NODE = self.getConfigNode(objectKey)
    except Exception:
      logger.error("Config corresponding to s3 object - " + objectKey + " not found")
      return
    oldConfig = os.path.join("/tmp/old" , objectKey)
    self.getConfig(OLD_CONFIG_NODE, OLD_CONFIG_PATH, oldConfig)
    configChangeDetector = configChangeNotifier.ConfigChangeDetector(oldConfig, newConfig)
    print "before check****"
    try:
      if not configChangeDetector.compareConfig():
        config_diff = configChangeDetector.getDiff()
        print "config_diff : ", open(config_diff, 'r').readlines()
        ''' notify any change to registered user along 
          with objectKey and diff files if apply_flag is False 
          else apply the change on the related node'''
        if apply_flag:
          self.applyChange(newConfig, OLD_CONFIG_NODE, OLD_CONFIG_PATH)
        else:
          print "diff computed"
          '''call mail server to send notification with diff files and objectKey and old config node and path.'''
          self.notifyConfigChange(objectKey, config_diff)
    except OSError as error:
      print "no file corresponding to object key ", objectKey
      pass

  def getAllS3Objects(self):
    print "Inside getAllS3Objects"
    return self.s3Dao.getAllObjects()

  def getS3Object(self, objectKey, newConfig):
    self.s3Dao.downloadObject(objectKey, newConfig)

  def getConfigPath(self, objectKey):
    print "object key ----", objectKey
    return helper.Helper.mapToPath(objectKey)

  def getConfigNode(self, objectKey):
    print "object key ----", objectKey
    return helper.Helper.mapToNode(objectKey)

  def getConfig(self, node, src_path, dest_path = None):
    print "node -----", node
    print "src path ----", src_path
    print "dest_path ----", dest_path
    return helper.Helper.copyConfig(os.path.join(self.configReader.getValue(self.SECTION, self.CONF_DIR), src_path), dest_path)
    #return helper.Helper.copyConfigFromRemote(node, src_path, dest_path)
    
  def applyChange(self, newConfig, node, path):
    configChangeNotifier.ConfigChangeApplier(newConfig, self.conf_dir, path)

  def notifyConfigChange(self, objectKey, ConfigDiff):
    server = self.configReader.getValue(self.SECTION, self.MAIL_SERVER)
    sender = self.configReader.getValue(self.SECTION, self.MAIL_SENDER)
    password = self.configReader.getValue(self.SECTION, self.MAIL_PASSWORD)
    receiver = self.configReader.getValue(self.SECTION, self.MAIL_RECEIVER)
    http_proxy_addr = self.configReader.getValue(self.SECTION, self.HTTP_PROXY_ADDR)
    http_proxy_port = self.configReader.getValue(self.SECTION, self.HTTP_PROXY_PORT)
    subject = self.configReader.getValue(self.SECTION, self.MAIL_SUBJECT) + ":S3 Object Key:" + objectKey 
    text = helper.Helper.getFileContents(ConfigDiff)
    
    mail = mailServer.MailServer(server, sender, password, http_proxy_addr, http_proxy_port)
    mail.sendMessage(receiver, subject, text)
    return subject + "\001" + text

import sys
if __name__ == '__main__':
  if len( sys.argv) < 2:
    print "Config File path required"
    sys.exit(-1)
  configManager = ConfigManager(sys.argv[1])
  configManager.reportAllConfigChange()
