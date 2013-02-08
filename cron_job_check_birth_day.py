#!/usr/bin/python
# -*- coding: utf-8 -*-   
# -- coding: iso-8859-15 --

from google.appengine.dist import use_library
use_library('django', '1.2')

import os
import cgi
import datetime
import urllib
import wsgiref.handlers
from operator import itemgetter, attrgetter

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import mail

import sys;
import re,urllib,urllib2;

from customer import Customer;

import config;
			
class checkBirthDay(webapp.RequestHandler):
	def get(self):
		today=datetime.datetime.today();
		query = db.GqlQuery("SELECT * FROM Customer Where birth_day=:1 and birth_month=:2",today.day,today.month);
		customerList=[cus for cus in query];
		
		if len(customerList)==0:
			self.response.out.write("No Cusomter Bithday=Today Found!");
			return;
		self.response.out.write("Found "+str(len(customerList))+" Cusomter Bithday=Today!");
		message = mail.EmailMessage()
		message.sender = "Caramel-Shop Admin <tranvietanh1991@gmail.com>"
		message.subject = "Today you have "+str(len(customerList))+" customer to happy bithday!"
		
		message.body = "This is list of customer:\n";
		for cus in customerList:
			message.body +="Name: "+cus.name+"\nPhone: "+cus.phone+"\nEmail: "+str(cus.email);
			message.body +="\n\n\n";
		message.body += "\nP/s: Do not reply to this email!";
		
		#send to all email in staff list
		for userEmail in config.special_user_dict:
			if userEmail == "tranvietanh1991@gmail.com":continue;
			message.to = userEmail;
			message.send();
		
		self.response.out.write("Emails have been sent!");

def main():
	application = webapp.WSGIApplication([
	('/tasks/birthday_check/', checkBirthDay),
	], debug=True)

	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
