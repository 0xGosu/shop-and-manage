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

##os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'



from google.appengine.api import users

from google.appengine.api import mail

import res;
import check,config;


from order import Order;
from customer import Customer;

class User(db.Model):
	email =  db.StringProperty();
	created = db.DateTimeProperty();
	who_created = db.UserProperty();
	modified = db.DateTimeProperty();
	who_modified = db.UserProperty();
	classify = db.StringProperty(choices=('User', 'Employee', 'Manager', 'Admin'));
	customer_code = db.StringProperty();

class custom:
	pass	

class UserPage(webapp.RequestHandler):
	def get(self):
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);
		#go back to home if no user
		if not user:self.redirect('/');
		else:	
			#find customer of user
			try:
				customer=db.get(db.Key.from_path('Customer',user.email()));
			except:
				customer=None;
			
			#find order
			info_table=[];
			total=0;
			
			if customer:
				status="Đây là tài khoản Khách Hàng của bạn!";
				#get all orders of customer
				order_query = db.GqlQuery("SELECT * FROM Order Where customer=:1 ORDER BY created DESC",customer.code);
				data = [order for order in order_query];
				
				#calculate money of orders
				for	order in data:
					row=custom();
					row.code=order.code;
					row.created=order.created;
					row.modified=order.modified;
					row.confirm=order.confirm;
					row.sum_money=sum([order.list_price[j]*order.list_quantity[j]for j in range(len(order.list_price))]);
					row.sum_quantity=sum(order.list_quantity);
					row.note= order.note;
					total+=row.sum_money;
					info_table+=[row];
					
			else: 
				status="Bạn chưa có tài khoản Khách Hàng! Mua bất kì 1 sản phẩm nào sẽ có ngay!";
			
			#render
			template_values = {
				'greeting': greeting,
				'user_class': user_class,
				'url_linktext': url_linktext,
				'user':user,
				'status':status,
				'customer':customer,
				'orders':info_table,
				'total':total,
			}

			path = os.path.join(os.path.dirname(__file__), 'user_info.html')
			self.response.out.write(template.render(path, template_values))

def main():
	application = webapp.WSGIApplication([
	('/user/', UserPage),
	], debug=True)

	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
