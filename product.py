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

from google.appengine.api import mail

import check;
import config;

class custom:
	index=0;

class Product(db.Model):
	"""Models an individual text Entry """
	created = db.DateTimeProperty();
	who_created = db.UserProperty();
	modified = db.DateTimeProperty();
	who_modified = db.UserProperty();
	category = db.StringProperty(default=config.category_list[0]);
	on_sale = db.IntegerProperty(default=0);
	code = db.StringProperty();
	spec_choices = db.ListProperty(str,default=[]);
	quantity = db.IntegerProperty(default=0);
	root_price = db.FloatProperty(default=0.0);
	sell_price = db.FloatProperty(default=0.0);
	description = db.StringProperty();
	detail = db.TextProperty();
	note = db.TextProperty();
	photo = db.StringProperty();

######## Use case ############
#http://yuml.me/edit/34203294
######### Class ##############
#http://yuml.me/edit/db7cc4a0
##############################


class ManageProduct(webapp.RequestHandler):
	def get(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);

		#check user are shoping or not
		shop=self.request.get('shop');

		#Only manager are allowed to access product part
		if(user_class != 'manager' and not shop):
			#render
			template_values = {
			'greeting': greeting,
			'user_class': user_class,
			'url_linktext': url_linktext,
			'detail' : "Limited Access!",
			}
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return

		#Get var from request
		code=self.request.get('code');

		#Query
#		if(tag):
#			query.filter("tag =", tag);
#		if(dhours and dminutes):
#			timeFilter=datetime.datetime.now()-datetime.timedelta(hours=int(dhours),minutes=int(dminutes) );
#			query.filter("date >",timeFilter);
#		query.order("-date");

		status="Quan Ly San Pham!";
		#check empty string
		if(code):
			product=db.get(db.Key.from_path("Product",code));
		else:
			product=None;
		#find product
		if product:
			status="Tim Thay!";
			spec_choices_str=','.join(product.spec_choices);
		else:
			status="Ko tim thay!";
			spec_choices_str='';

		#render
		template_values = {
			'greeting': greeting,
			'user_class': user_class,
			'url_linktext': url_linktext,
			'status':status,
			'product':product,
			'spec_choices_str':  spec_choices_str,
			'category_list':config.category_list,
		}

		if shop:
			category_name=self.request.get('category');
			#find information about category
			category_header=check.category_info_of(category_name);

			#clear status if there is product
			if product:template_values['status']='';

			#find submenu of category
			sub_menu_header,sub_menu=check.sub_menu_of(category_name);
			
			if(sub_menu_header=="Thời Trang Nữ"):
				template_values.update({
				'current_page':'female',
				'link_content_poster':'/images/beauty-care.jpg',
				});
			elif(sub_menu_header=="Thời Trang Nam"):
				template_values.update({
				'current_page':'male',
				'link_content_poster':'/images/beauty-care.jpg',
				});
			else:
				template_values.update({
				'current_page':'other',
				'link_content_poster':'/images/beauty-care.jpg',
				});
			
			template_values.update({
			'category_header':category_header,
			'sub_menu_header':sub_menu_header,
			'sub_menu_list':sub_menu,
			});
			path = os.path.join(os.path.dirname(__file__), 'shop_product.html')
			self.response.out.write(template.render(path, template_values))
		else:
			path = os.path.join(os.path.dirname(__file__), 'product.html')
			self.response.out.write(template.render(path, template_values))

	def post(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);
		template_values = {
			'greeting': greeting,
			'user_class': user_class,
			'url_linktext': url_linktext,
		}
		if(user_class != 'manager'):
			#render
			template_values.update({
			'detail' : "Limited Access!",
			});
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return

		#Get var from request and pass to data model object
		code=self.request.get('code');
		action=self.request.get('action');

		#Query
#		query = db.Query(Product, keys_only=False);
#		query.filter("code =", code);
#		data = query.fetch(1);
		product=db.get(db.Key.from_path("Product",code));
		status="";
		if product:
			status="Sua thong tin thanh cong!";
			
			if(action and action!='modify'):
				#render
				template_values.update({
				'detail' : "Thao tac sai! (San pham "+code+" da co trogn CSDL)",
				});
				path = os.path.join(os.path.dirname(__file__), 'error.html')
				self.response.out.write(template.render(path, template_values))
				return
		else:
			status="Create Product Success!";
			
			if(action and action!='create'):
				#render
				template_values.update({
				'detail' : "Thao tac sai! (San pham "+code+" chua co trong CSDL)",
				});
				path = os.path.join(os.path.dirname(__file__), 'error.html')
				self.response.out.write(template.render(path, template_values))
				return
				
			product = Product(key_name=code);
			product.created = datetime.datetime.now();
			product.who_created=user;
			product.code = code;

		product.modified = datetime.datetime.now();
		product.who_modified = user;
		product.category = self.request.get('category');
		try:
			product.on_sale = int( self.request.get('on_sale') );
		except:
			product.on_sale = 0;

		#product.size = self.request.get('size');
		#product.color= self.request.get('color');
		#get list spec_choices from request by split ,
		if(self.request.get('spec_choices_str')):product.spec_choices=self.request.get('spec_choices_str').split(',');

		product.quantity = int( self.request.get('quantity') );
		product.root_price = float( self.request.get('root_price') );
		product.sell_price = float( self.request.get('sell_price') );
		product.description = self.request.get('description');
		product.detail =  db.Text( self.request.get('detail') );
		product.photo = self.request.get('photo');
		product.note = self.request.get('note');
		product.put() #save data model object to data base

		#render
		template_values.update({
			'status':status,
			'product':product,
			'spec_choices_str':  ','.join(product.spec_choices),
			'category_list':config.category_list,
		});

		path = os.path.join(os.path.dirname(__file__), 'product.html')
		self.response.out.write(template.render(path, template_values))

class ListProduct(webapp.RequestHandler):
	def get(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);
		#check user are shoping or not
		shop=self.request.get('shop');
		#check client requesting service
		client=self.request.get('client');
		#check is this a qr-code print version
		qrcode_print=self.request.get('qrcode_print');
		qrcode_size=self.request.get('qrcode_size');
		
		#check access
		if(user_class != 'manager' and not shop and client!='mobile'):
			#render
			template_values = {
			'greeting': greeting,
			'user_class': user_class,
			'url_linktext': url_linktext,
			'detail' : "Limited Access!",
			}
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return

		#Get var from request
		try:
			max=int(self.request.get('max'));
		except:
			max=200;
		try:
			page=int(self.request.get('page'));
		except:
			page=0;

		#Get sort and filter atribute
		sort_by=self.request.get('sort_by');
		category_filter=self.request.get('category_filter');
		spec_filter=self.request.get('spec_filter');




		#Query
		query = db.Query(Product, keys_only=False);
		#filter
		if(category_filter):query.filter('category =', category_filter);
		if(spec_filter):query.filter('spec_choices =', spec_filter);
		
		#if(shop):query.filter('photo !=','');#filter so that only products with photo are show on website
		if(shop=='sale'):query.filter('on_sale >',0);
		
		#sort
		if(sort_by=='created'):query.order('-created');
		elif(sort_by=='on_sale'):query.order('-on_sale');

		if(max<20):max=20;
		if(page<0):page=0;
		
		#fetch all if client = mobile
		if(client=='mobile'):data=query.fetch(query.count(None));
		else:data = query.fetch(max,page*max);

		status="Day la nhung san pham tu "+str(page*max)+" toi "+str(page*max+len(data));
		if(len(data)==max):status+=" - Bam tiep de xem nhieu hon!";
		#if(shop):status+=" - Products with no photo are hidden!";
		
		#save var from request to pass to template
		request=custom();
		request.max=max;request.page=page;
		request.category_filter=category_filter;
		request.spec_filter=spec_filter;
		request.sort_by=sort_by;
		request.qrcode_size=qrcode_size;
		request.shop=shop;
		
		#render
		template_values = {
			'request':request,
			'user_class':user_class,
			'greeting': greeting,
			'user_class': user_class,
			'url_linktext': url_linktext,
			'status':status,
			'products':data,
			'category_list':config.category_list,
		}
		if shop:
			if shop=='new': #Menu of Hang Moi Ve
				category_header=sub_menu_header="Hang Moi Ve";
				sub_menu=[{
						  'link':"/product/list/?shop=new&sort_by=created&category_filter="+config.category_list[iter],
						  'text':config.category_header[iter],
						  }for iter in range(len(config.category_list))]
				template_values.update({
				'current_page':'new',
				'link_content_poster':'/images/apparel.jpg',
				});
			elif shop=='sale': #Menu of Hang Sale
				category_header=sub_menu_header="Hang SALE!!!";
				sub_menu=[{
						  'link':"/product/list/?shop=sale&sort_by=on_sale&category_filter="+config.category_list[iter],
						  'text':config.category_header[iter],
						  }for iter in range(len(config.category_list))]
				template_values.update({
				'current_page':'sale',
				'link_content_poster':'/images/beauty-care.jpg',
				});
			else: # normal case
				#find information about category
				category_header=check.category_info_of(category_filter);
				#find submenu of category
				sub_menu_header,sub_menu=check.sub_menu_of(category_filter);
				if(sub_menu_header=="Thời Trang Nữ"):
					template_values.update({
					'current_page':'female',
					'link_content_poster':'/images/beauty-care.jpg',
					});
				elif(sub_menu_header=="Thời Trang Nam"):
					template_values.update({
					'current_page':'male',
					'link_content_poster':'/images/beauty-care.jpg',
					});
				else:
					template_values.update({
					'current_page':'other',
					'link_content_poster':'/images/beauty-care.jpg',
					});

			template_values.update({
			'category_header':category_header,
			'sub_menu_header':sub_menu_header,
			'sub_menu_list':sub_menu,
			});
			path = os.path.join(os.path.dirname(__file__), 'shop_list_product.html')
			self.response.out.write(template.render(path, template_values))
		elif qrcode_print:
			path = os.path.join(os.path.dirname(__file__), 'qr-code_list_product.html')
			self.response.out.write(template.render(path, template_values))
		elif client=='mobile':
			path = os.path.join(os.path.dirname(__file__), 'list_product_service.xml')
			self.response.out.write(template.render(path, template_values))
		else:
			path = os.path.join(os.path.dirname(__file__), 'list_product.html')
			self.response.out.write(template.render(path, template_values))


def main():
	application = webapp.WSGIApplication([
	('/product/', ManageProduct),
	('/product/list/', ListProduct),
	], debug=True)

	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
