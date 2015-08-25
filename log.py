#coding=utf-8
import os
# from model import Model
import time
class File:
	def __init__(self):
		pass

	def write_log(self,timenow, log_path, content):
		#检索出用户设置的目录，检查目录是否存在，如果不存在，新建
		if not os.path.exists(log_path):
			os.makedirs(log_path)
		#组成完整文件路径	
		file_path = log_path+"exec_"+timenow+".log"
		try:
			file = open(file_path, 'w+')
			file.write(content)
		except IOError:
			print "请检查log目录权限是否正常",e
		except:
			print "写入失败"
		finally:
			file.close()
		return file_path
		
#测试
if __name__ == '__main__':
	File(time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()) ,"123123123")