#coding=utf-8
import threading
import paramiko
import time
import Queue
from model import Model
import log


class Batch:
	def __init__(self):
		pass

	def do(self,server_id,shell_command):
		queue = Queue.Queue()
		for i in server_id:
			queue.put(i)
		#设置线程数量(如果任务小于50个，按照任务数量设置多线程，否则限制最大线程100)
		if len(server_id) < 30:
			self.for_ready(server_id,shell_command)
		else:
			threads_num = 70;
			#初始化列表
			sid = []
			while True:
				qsize = queue.qsize()
				if qsize > 0:
					for i in xrange(threads_num):
						if qsize > 0:
							sid.append(queue.get())
							# print "size %d"%queue.qsize()
						else:
							break
				else:
					break
				#发送任务给for_ready()后清空列表，防止重复		
				self.for_ready(sid,shell_command)
				del sid[:]

		#获取执行的时间
		#timenow = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
		#Model().select("select parameter_value from opt_system_parameter where parameter_name='exec_log_path'")
		#获取exec log目录路径
		sql = "insert into opt_exec_log (log_name, log_content, time) values ('%s','%s','%s')"%(shell_command,shell_command,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
		insert_log = Model().insert(sql)
		#循环结束之后记录日志
		#file_path = log.File().write_log(timenow, log_path[0][0], content)
		print insert_log

	#根据工作量创建进程
	def for_ready(self,server_id,shell_command):
		# print server_id
		threads = []
		for i in xrange(len(server_id)):
			user_data = Model().select("select ip,port,user from opt_machine where id=%s"%server_id[i])
			th = threading.Thread(target= self.thread_worker, args= (user_data[0][0], user_data[0][1], user_data[0][2], shell_command))
			threads.append(th)
			th.start()
		for i in threads:
			i.join()

	#SSH连接并执行命令
	def thread_worker(self,ip,port,user,shell_command):
		global content
		content = ''
		# print ip,port,user
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		# ssh.connect("121.40.59.144", 22, "root", "Rootadmin64")
		try:
			ssh.connect(ip, int(port), user, "Rootadmin64", timeout=1)
			stdin, stdout, stderr = ssh.exec_command(shell_command)
			content += time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())+"	"+ip+" :\n"+stdout.read()+"\n"
		except:
			content += "%s %s 连接失败\n"%(time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()),ip)
		ssh.close()

# 测试用
if __name__ == '__main__':
	Batch().do((1,2,3),"free -m")