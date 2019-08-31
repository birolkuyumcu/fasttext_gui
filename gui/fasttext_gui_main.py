# -*- coding: utf-8 -*-

#
# Copyright (c) 2017-present, Sefamerve R&D Center
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

"""

"""
import sys
from PySide import QtCore, QtGui,QtWebKit

from fasttext_ui import Ui_Dialog

import subprocess
import os
import sys
import threading
import numpy as np
import pygal

def make_bach_file(fname,command):
	fp = file(fname,'wt')
	fp.write(command)
	fp.close()
	
def check_number(txt,min_val,max_val,desc):
	msg =''
	try:
		val = float(txt)
		if val > max_val or  val < min_val:
			msg = '{0} value between ({1}, {2})'.format(desc,min_val, max_val)
	except:
		msg = '{0} is not valid'.format(desc,min_val, max_val)
		
	return msg
	
def draw_xy(fname,xvals,yvals):
	xy_chart = pygal.XY()
	xy_chart.title = u'Training progres vs loss '
	xy_chart.add('Loss',[(xvals[i],yvals[i]) for i in range(len(xvals))])
	xy_chart.render_to_file(fname+'.svg')	
	
def get_train_data(out):
	X = []
	Y = []	
	for i in range(7,len(out)):		
		l = out[i].split()
		if len(l) == 11 :
			X.append(float(l[1][:-1]))
			Y.append(float(l[7]))
		
	X = np.array(X)
	Y = np.array(Y)
	return X,Y
	
def filter_data(X,Y):
	xthresh = 0.1
	ythresh = 0.01
	xf = []
	yf = []		
	
	xprev = X[0]
	yprev = Y[0]
	
	xf.append(xprev)
	yf.append(yprev)	
	
	for i in range(1,len(X)):
		xcur = X[i]
		ycur = Y[i]
		if np.abs(xcur-xprev) >= xthresh or np.abs(ycur-yprev) >= ythresh :
			xprev = xcur
			yprev = ycur	
			xf.append(xprev)
			yf.append(yprev)
	
	xf = np.array(xf)
	yf = np.array(yf)
	return xf,yf	
	

class MyExecute(QtCore.QThread):
		
	def set_command(self,command):
		self.command = command
		self.out = ''
		
	def set_mod(self,mod):
		self.mod = mod
	
		
	def run(self):
		if self.mod == "std output":
			subprocess.check_call(self.command)
		else:
			if os.name == 'posix':
				bach_file =  'temp.sh'
			else:
				bach_file =  'temp.bat'
			
			make_bach_file(bach_file,self.command)
			p2 = subprocess.Popen(bach_file.split(' '),stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
			out,temp = p2.communicate()
			self.out = out.splitlines()
			print self.out,'\n\n',temp
		self.emit(QtCore.SIGNAL("processEnd()"))

class FastTextForm(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		# 
		commands = ["skipgram","cbow","supervised","test"]
		for command in commands:
			self.ui.comboBoxCommand.addItem(command)
		#
		loss_funcs = ["ns","hs","softmax"]
		for loss in loss_funcs:
			self.ui.comboBoxLoss.addItem(loss)	
			
		#
		modes = ["slient","std output"]
		for mod in modes:
			self.ui.comboBoxMode.addItem(mod)	
		#		
		self.myex = MyExecute()
		timer = QtCore.QTimer(self)
		self.connect(timer, QtCore.SIGNAL("timeout()"), self.update)
		timer.start(1000)
		
		#
		
		display = QtGui.QLabel(self.ui.tabWidget.widget(1))
		display.setGeometry(55,10,630,320)
		display.setFrameStyle(QtGui.QFrame.Panel )
		
		self.view = QtWebKit.QWebView(self.ui.tabWidget.widget(1))
		self.view.setGeometry(56,11,628,318)
		self.view.show()
		#
		self.dir = os.getcwd()
		self.fDialog = QtGui.QFileDialog(self)
		self.fname =''
		self.is_auto_tested = False
		
	@QtCore.Slot()
	def on_pushButtonRun_clicked(self):
		self.ui.listWidget.clear()
		if self.checkInputs() :		
			self.setCommand()
			self.ui.listWidget.addItem(self.command)
			
			self.myex.set_command(self.command)
			self.myex.set_mod(self.ui.comboBoxMode.currentText())
			self.connect(self.myex,QtCore.SIGNAL("processEnd()"),self.processEnd)
			self.myex.start()
			self.ui.pushButtonRun.setEnabled(False)
			self.ui.pushButtonStop.setEnabled(True)
			self.ui.progressBar.setValue(0)		
			
	@QtCore.Slot()
	def on_pushButtonZoom_clicked(self):
		if os.path.exists(self.fname+'.svg'):
			zdialog = QtGui.QDialog()
			webView = QtWebKit.QWebView(zdialog)
			zdialog.setWindowTitle('Zoom')
			webView.load(QtCore.QUrl(self.fname+'.svg'))
			webView.show()
			zdialog.exec_()		
		
	@QtCore.Slot()
	def on_pushButtonStop_clicked(self):
		if self.myex.isRunning():
			print 'exiting thread'
			self.myex.setTerminationEnabled() 
			self.myex.terminate()
			self.ui.listWidget.addItem('exiting thread')
			self.processEnd()
			self.ui.pushButtonStop.setEnabled(False)
		
	@QtCore.Slot()
	def on_toolButtonTextFile_clicked(self):
		print 'Text File'
		fileName = self.fDialog.getOpenFileName(self,"Select Text or Corpus File ", self.dir, "(*.*)")
		if fileName[0] == u'':
			return
		self.dir = os.path.dirname(fileName[0])
		self.ui.lineEditTextFile.setText(fileName[0])		
		
	@QtCore.Slot()
	def on_toolButtonModelFile_clicked(self):
		print 'Model File'
		fileName = self.fDialog.getOpenFileName(self,"Select Model File ", self.dir, "(*.*)")
		if fileName[0] == u'':
			return
		self.dir = os.path.dirname(fileName[0])
		self.ui.lineEditModelFile.setText(fileName[0])			
	

		
	def closeEvent(self,event):
		print 'Exiting'
		
	def setCommand(self):
		if (self.ui.comboBoxCommand.currentText() == 'test') :
			if os.name == 'posix':			
				self.command = './fasttext test'
			else:
				self.command = 'fasttext test'
				model_file =self.ui.lineEditModelFile.text()
				if not '.bin' in model_file and not '.ftz' in model_file:
					model_file +='.bin'
			self.command = self.command + ' ' + model_file + ' ' +self.ui.lineEditTextFile.text()
		
		else:
			command_list = []
			if os.name == 'posix':			
				command_list.append('./fasttext')
			else:
				command_list.append('fasttext')
			command_list.append(self.ui.comboBoxCommand.currentText())
			command_list.append('-input '+self.ui.lineEditTextFile.text())
			command_list.append('-output '+self.ui.lineEditModelFile.text())
			command_list.append('-lr '+self.ui.lineEditLR.text())
			command_list.append('-lrUpdateRate '+self.ui.lineEditLRUpdate.text())
			command_list.append('-epoch '+self.ui.lineEditEpoch.text())
			command_list.append('-dim '+self.ui.lineEditDim.text())
			command_list.append('-loss '+self.ui.comboBoxLoss.currentText())
			command_list.append('-wordNgrams '+self.ui.lineEditWordNgrams.text())			
			command_list.append('-neg '+self.ui.lineEditNeg.text())			
			command_list.append('-ws '+self.ui.lineEditContextWindow.text())
			command_list.append('-minCount '+self.ui.lineEditMinWord.text())
			command_list.append('-minCountLabel '+self.ui.lineEditMinLabel.text())			
			command_list.append('-t '+self.ui.lineEditThreshold.text())				
			command_list.append('-bucket '+self.ui.lineEditBucket.text())			
			command_list.append('-minn '+self.ui.lineEditMinCharNG.text())			
			command_list.append('-maxn '+self.ui.lineEditMaxCharNG.text())				
			command_list.append('-thread '+self.ui.lineEditThreads.text())				
			self.command = ' '.join(command_list)
			self.is_auto_tested = False
			
	def checkInputs(self):
		msg =''
		ret = True
		if (self.ui.comboBoxCommand.currentText() == 'test') :
			fname = self.ui.lineEditModelFile.text()
			if not '.bin' in fname and not '.ftz' in fname:
				fname +='.bin'			
			if not os.path.exists(fname) :
				msg = fname + ' not found'
				
			fname = self.ui.lineEditTextFile.text()
			if not os.path.exists(fname) :
				msg = fname + ' not found'
			

		else:
			temp = self.ui.lineEditLR.text()
			msg = check_number(temp,0,1,'Learning Rate')
			temp = self.ui.lineEditLRUpdate.text()
			msg = check_number(temp,1,100,'Learning Rate Update')
			temp = self.ui.lineEditEpoch.text()
			msg = check_number(temp,1,1000000,'Epoch')	
			temp = self.ui.lineEditDim.text()
			msg = check_number(temp,25,2000,'Size of word vectors')	
			temp = self.ui.lineEditWordNgrams.text()
			msg = check_number(temp,1,7,'max length of word ngram')
			temp = self.ui.lineEditNeg.text()
			msg = check_number(temp,3,10,'number of negatives sampled')	
			temp = self.ui.lineEditContextWindow.text()
			msg = check_number(temp,1,20,'size of the context window')	
			temp = self.ui.lineEditMinWord.text()
			msg = check_number(temp,1,100,'minimal number of word occurences')	
			temp = self.ui.lineEditMinLabel.text()
			msg = check_number(temp,1,100,'minimal number of label occurences')			
			temp = self.ui.lineEditThreshold.text()
			msg = check_number(temp,0,0.1,'sampling threshold')				
			temp = self.ui.lineEditBucket.text()
			msg = check_number(temp,100,5000000,'number of buckets')				
			temp = self.ui.lineEditMinCharNG.text()
			msg = check_number(temp,1,10,'min length of char ngram')			
			temp = self.ui.lineEditMaxCharNG.text()
			msg = check_number(temp,1,10,'max length of char ngram')			
			temp = self.ui.lineEditThreads.text()
			msg = check_number(temp,1,20,'number of thread')					
			
		if msg != '':
			self.showError(msg)
			ret = False			
	
		return ret
	
		
	def update(self):
		if self.myex.isRunning():
			self.ui.progressBar.setValue((self.ui.progressBar.value()+1)%100)
		
	
	def processEnd(self):
		self.ui.pushButtonRun.setEnabled(True)
		self.isRunning = False
		self.ui.progressBar.setValue(100)
		if len(self.myex.out) < 50:
			for oline in self.myex.out :
				self.ui.listWidget.addItem(oline)			
		else:
			for oline in self.myex.out[:20] :
				self.ui.listWidget.addItem(oline)
			self.ui.listWidget.addItem('...')	
			for oline in self.myex.out[-10:] :
				self.ui.listWidget.addItem(oline)			
			
		X,Y = get_train_data(self.myex.out)
		if len(X) > 2:
			self.fname = self.ui.lineEditModelFile.text()			
			self.save_log()
			X,Y = filter_data(X,Y)
			draw_xy(self.fname,X,Y)			
			self.view.load(self.fname+'.svg')
			self.view.show()
		if not self.is_auto_tested and (self.ui.comboBoxCommand.currentText() == 'supervised') :
			self.auto_test()
			self.is_auto_tested = True
		else:
			pass 
			

		
	def showError(self,msg):
		QtGui.QMessageBox.warning(self,'FastText GUI',msg)
		
	def save_log(self):
		f =open(self.fname+'.log','w')
		f.write(self.command+ '\n')
		for oline in self.myex.out :
			f.write(oline+ '\n')
		f.close()
		
	def auto_test(self):
		print "Auto test started "
		fname = self.ui.lineEditTextFile.text()
		if fname[-6:] == '.train':				
			fname = fname.replace('.train','.test')
			if os.path.exists(fname) :
				self.ui.listWidget.addItem("auto test mode started with "+fname)				
				if os.name == 'posix':			
					self.command = './fasttext test'
				else:
					self.command = 'fasttext test'
					model_file =self.ui.lineEditModelFile.text()
					if not '.bin' in model_file:
						model_file +='.bin'
				self.command = self.command + ' ' + model_file + ' ' +fname				
				self.myex.set_command(self.command)	
				self.myex.set_mod(self.ui.comboBoxMode.currentText())
				self.connect(self.myex,QtCore.SIGNAL("processEnd()"),self.processEnd)
				self.myex.start()	
			else:
				print "Not found ",fname


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    monitor = FastTextForm()
    monitor.show()
    sys.exit(app.exec_())
