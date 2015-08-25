#coding=utf-8
import MySQLdb

class Model():
	def __init__(self):
		#初始化 MySQL 连接
		global conn
		global cur
		try:
			conn= MySQLdb.connect(host='localhost',port = 3306,user='root',passwd='',db ='opt_system')
			cur = conn.cursor()
		except:
			print "Mysql连接失败"
		
	def select(self,sql):
		try:
			count = cur.execute(sql)
			data = cur.fetchall()
			#print data
			return data
		except Exception as e :
			print "Mysql查询失败",e

	def insert(self,sql):
		try:
			count = cur.execute(sql)
			result = conn.commit()
			return result
		except:
			print "Mysql插入失败"

	def __del__(self):
		#操作完成释放 MySQL 连接
		cur.close()
		conn.close()