#!/usr/bin/python
# -*- coding: utf-8 -*-   
# -- coding: iso-8859-15 --

from google.appengine.dist import use_library
use_library('django', '1.2')

import os
import cgi
import datetime,re
import urllib,urllib2
import wsgiref.handlers
from operator import itemgetter, attrgetter

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util


from google.appengine.api import users

from google.appengine.api import mail

import check;
import product;
from customer import Customer;

class trow:
	index=0;
	
class custom:
	pass

class Order(db.Model):
	"""Models an individual text Entry """
	created = db.DateTimeProperty();
	who_created = db.UserProperty();
	modified = db.DateTimeProperty();
	who_modified = db.UserProperty();
	code = db.StringProperty();
	customer = db.StringProperty();
	list_item = db.ListProperty(str,default=['']*15);
	list_price = db.ListProperty(float, default=[0.0]*15);
	list_root_price = db.ListProperty(float, default=[0.0]*15);
	list_quantity = db.ListProperty(int, default=[0]*15);
	list_chosen = db.ListProperty(str,default=['']*15);
	note = db.TextProperty();
	confirm = db.BooleanProperty(default=False);
	hidden = db.BooleanProperty(default=False);

######## Use case ############
#http://yuml.me/edit/41f0c516
######### Class ##############
#http://yuml.me/edit/fe26f7bb
##############################


class ManageOrder(webapp.RequestHandler):
	def get(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);
		
		#check user are shoping or not
		shop=self.request.get('shop');
		#check client requesting service
		client=self.request.get('client');
		
		if(user_class not in ['manager','employee'] and not shop and client != 'mobile'):
			#render
			template_values = {
			'greeting': greeting,
			'user_class':user_class,
			'url_linktext': url_linktext,
			'detail' : "Limited Access!",
			}
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return

		#Get var from request
		code=self.request.get('code');
		
		info_table=[];
		total=0;
		customer=None;

		if(shop and not code):#show order saveed on cookie
			cookies=self.request.cookies;
			for key in cookies:
				cookies[key]=urllib2.unquote(cookies[key].encode('utf-8'));
			if(cookies.has_key('cart_item')):
				list_item=cookies['cart_item'].split(',');
				list_chosen=cookies['cart_chosen'].split(',');
				list_quantity=cookies['cart_quantity'].split(',');
			else:
			   list_item=list_chosen=list_quantity=[];
			
			if user:customer=db.get(db.Key.from_path('Customer',user.email()));
			for	i in range(10):
				if i>=len(list_item):break;
				#find product by code in list_item
				photo='';
				row_status='';
				item=None;
				if list_item[i]:
					item=db.get(db.Key.from_path('Product',list_item[i]));
					if item:
						row_status="Sản Phẩm có trong CSDL";
						if(item.on_sale):row_status+=" với "+str(item.on_sale)+"% sale off";
						photo=item.photo;
					else:
						continue;
				else:
					continue;

				row=trow();
				row.index=i;
				row.photo=photo;

				row.spec_choices=[];
				#current choice
				row.chosen=list_chosen[i];
				#other available choice
				if(item):row.spec_choices=item.spec_choices;


				row.item=list_item[i];
				
				# price = item.sell_price*(1-item.on_sale% or customer.private_sale%)
				sale_off=0;
				if customer:sale_off=customer.private_sale;
				if item.on_sale:sale_off= item.on_sale;
				if sale_off>100:sale_off=100;
				row.price=item.sell_price*(1-float(sale_off)/100);
				
				row.quantity=list_quantity[i];
				
				row.money=row.price*int(row.quantity);
				total+=row.money;
				
				row.status=row_status;

				info_table+=[row];
			
		####################################################################################
		status="Quản Lý Đơn Hàng!";
		list_price=[];
		#check empty string
		try:
			order=db.get(db.Key.from_path('Order',int(code)));
		except:
			order=None;

		#find order
		if order:
			status="Tìm Thấy!";
			if order.customer:
				customer=db.get(db.Key.from_path('Customer',order.customer));
			#get list_price from list_item
			for	i in range(10):
				#find product by code in list_item
				photo='';
				row_status='';
				item=None;
				if order.list_item[i]:
					item=db.get(db.Key.from_path('Product',order.list_item[i]));
					if item:
						row_status="Sản Phẩm có trong CSDL";
						if(item.on_sale):row_status+=" với "+str(item.on_sale)+"% sale off";
						photo=item.photo;
					else:
						row_status="Ko tìm thấy!";
				else:
					row_status="x";

				row=trow();
				row.index=i;
				row.photo=photo;

				row.spec_choices=[];
				#current choice
				row.chosen=order.list_chosen[i]
				#other available choice
				if(item):row.spec_choices=item.spec_choices;


				row.item=order.list_item[i];
				row.price=order.list_price[i];
				row.quantity=order.list_quantity[i];
				try:
					row.money=row.price*row.quantity;
					total+=row.money;
				except:
					row.money="?";
				row.status=row_status;

				info_table+=[row];

			#status+=" item="+str(len(info_table));
		elif not shop:
			status="Ko tìm thấy!";
			for i in range(10):
				row=trow();
				row.index=i;
				row.price='x';
				row.quantity=0;
				row.status='x';
				info_table+=[row];

		if not code:status="Quản Lý Đơn Hàng!";
		if self.request.get('status'):status=self.request.get('status');

		#fix date.created to GMT+7 for bill print
		if order:date_plus7=order.created + datetime.timedelta(hours=7);
		else:date_plus7=datetime.datetime.now() + datetime.timedelta(hours=7);
		#render
		template_values = {
			'greeting': greeting,
			'user_class':user_class,
			'url_linktext': url_linktext,
			'user':user,
			'status':status,
			'order':order,
			'customer':customer,
			'info_table':info_table,
			'total':total,
			'date_plus7':date_plus7,
		}

		if self.request.get('version')=='print':
			path = os.path.join(os.path.dirname(__file__), 'bill.html')
			self.response.out.write(template.render(path, template_values))
			return
		if shop:
			path = os.path.join(os.path.dirname(__file__), 'shop_order.html')
			self.response.out.write(template.render(path, template_values))
			return
		path = os.path.join(os.path.dirname(__file__), 'order.html')
		self.response.out.write(template.render(path, template_values))

	def post(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);
		
		#check user are shoping or not
		shop=self.request.get('shop');
		#check client requesting service
		client=self.request.get('client');
		
		if(user_class not in ['manager','employee'] and not shop and client!='mobile'):
			#render
			template_values = {
			'greeting': greeting,
			'user_class':user_class,
			'url_linktext': url_linktext,
			'detail' : "Limited Access!",
			}
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return

		#Get var from request and pass to data model object
		code=self.request.get('code'); 
		
		#shoping user cant mofify order
		if(shop and code): 
			#render
			template_values = {
			'greeting': greeting,
			'user_class':user_class,
			'url_linktext': url_linktext,
			'detail' : "Limited Access!",
			}
			path = os.path.join(os.path.dirname(__file__), 'error.html')
			self.response.out.write(template.render(path, template_values))
			return
		
		#Query
#		query = db.Query(Product, keys_only=False);
#		query.filter("code =", code);
#		data = query.fetch(1);
		try:
			order=db.get(db.Key.from_path('Order',int(code)));
		except:
			order=None;

		status='';
		if order:
			status="Sửa thông tin thành công!";
		else:
			status="Tạo Đơn Hàng thành công!";
			order = Order();
			order.created = datetime.datetime.now();
			order.who_created = user;
			#save order to get auto generated code
			order.put();
			order.code = str(order.key().id());

		order.modified = datetime.datetime.now();
		order.who_modified = user;
		#get customer of order
		try:customer=db.get(db.Key.from_path('Customer',order.customer));
		except:customer=None;

		#freely to change if confirm is false
		if not order.confirm:
			try:
				order.confirm = bool( self.request.get('confirm') );
			except:
				pass
			#get list_item and list_quantity, list_chosen (and make changes to database if confirm = true
			for i in range(15):
				#save last item code
				prev_item_code=order.list_item[i];
				#get new item code
				order.list_item[i]=self.request.get('item'+str(i));
				try:order.list_price[i]=float(self.request.get('price'+str(i)));
				except:pass
				# get price if item code change
				try:
					item=db.get(db.Key.from_path('Product',order.list_item[i]));
				except:
					item=None;


				#clear price when no product code
				if not item:
					order.list_price[i]=0.0;
				#update quantity and spec chosen
				try:
					order.list_quantity[i]=int( self.request.get('quantity'+str(i)) );
				except:
					order.list_quantity[i]=0;
				order.list_chosen[i]=self.request.get('chosen'+str(i)) ;
				
				#clear spec_chosen when phoduct code change (except for the case shop , client mobile) or product code = '' 
				if(not shop and client!='mobile' and prev_item_code != order.list_item[i] or order.list_item[i]=='' ) :order.list_chosen[i]='';

                #only update price when product code changes
				if item and prev_item_code != order.list_item[i]:
					# price = item.sell_price*(1-item.on_sale% or customer.private_sale%)
					sale_off=0;
					if customer:sale_off=customer.private_sale;
					if item.on_sale:sale_off= item.on_sale;
					if sale_off>100:sale_off=100;
					order.list_price[i]=item.sell_price*(1-float(sale_off)/100);
					
                    # also make quantity = 1 if quantity=0
					if not order.list_quantity[i]:order.list_quantity[i]=1;

				#check for remove quantity and spec_choice from database when confirm change from false to true. If cant remove, confirm order = false.
				if item and order.confirm:
					if(item.quantity<order.list_quantity[i]) or (item.spec_choices and order.list_chosen[i] not in item.spec_choices):
						status="Đơn hàng này ko xác nhận được! Kiểm tra lại các thông tin sản phẩm!";
						order.confirm=False;
			#get var from request
			try:
				order.hidden =  bool( self.request.get('hidden') );
			except:
				order.hidden = False;
			
			
			#actually remove quantity and spec_choice from database
			if order.confirm:
				for i in range(15):
					try: item=db.get(db.Key.from_path('Product',order.list_item[i]));
					except: continue;
					if(not item):continue;
					#save root_price at the time product being sold
					order.list_root_price[i]=item.root_price;
					#change and save item
					item.quantity-=order.list_quantity[i];
					for iter0 in range(order.list_quantity[i]):
						try:item.spec_choices.remove(order.list_chosen[i]);
						except:pass
					item.put();
				#make hidden = False ( confirmed order cant be hidden)
				order.hidden=False;

			#get var from request
			order.customer=self.request.get('customer');
			try:
				order.note =  db.Text( self.request.get('note') );
			except:
				order.note ="";


		#order is confirmed, cant change but only unconfirmed.
		if order.confirm:
			try:
				order.confirm = bool( self.request.get('confirm') );
			except:
				pass
			if order.confirm:
				status="Đơn hàng này đã được xác nhận! Thông tin sẽ ko thể thay đổi cho tới khi hủy xác nhận!"
			else:#unconfirming order
				#undo the changes from database and get list_item and list_quantity, list_chosen
				for i in range(15):
					#save last item code
					prev_item_code=order.list_item[i];
					#get new item code
					order.list_item[i]=self.request.get('item'+str(i));
					try:
						item=db.get(db.Key.from_path('Product',order.list_item[i]));
					except:
						item=None;
					#undo the changes from database when confirm change from true to false.
					#find prev item
					if prev_item_code == order.list_item[i]:prev_item=item;
					elif prev_item_code:prev_item=db.get(db.Key.from_path('Product',prev_item_code));
					if prev_item:
						#undo changes and save
						prev_item.quantity+=order.list_quantity[i];
						for iter0 in range(order.list_quantity[i]):prev_item.spec_choices+=[ order.list_chosen[i] ];
						prev_item.put();

					#Get price
					try:order.list_price[i]=float(self.request.get('price'+str(i)));
					except:pass
					#only update price when product code changes
					if item and prev_item_code != order.list_item[i]:
						# price = item.sell_price*(1-item.on_sale% or customer.private_sale%)
						sale_off=0;
						if customer:sale_off=customer.private_sale;
						if item.on_sale:sale_off= item.on_sale;
						if sale_off>100:sale_off=100;
						order.list_price[i]=item.sell_price*(1-float(sale_off)/100);
						


					#update quantity and spec chosen
					try:
						order.list_quantity[i]=int( self.request.get('quantity'+str(i)) );
					except:
						order.list_quantity[i]=0;
					order.list_chosen[i]=self.request.get('chosen'+str(i)) ;



				order.customer=self.request.get('customer');
				try:
					order.note =  db.Text( self.request.get('note') );
				except:
					order.note ="";
				try:
					order.hidden =  bool( self.request.get('hidden') );
				except:
					order.hidden = False;


		order.put() #save data model object to data base
		#create account at first time user send an order 
		if(shop and order.customer and not customer):
			customer = Customer(key_name=order.customer);
			customer.created = datetime.datetime.now();
			customer.who_created = user;
			customer.code = order.customer;
			customer.email=db.Email(order.customer);
			customer.modified = datetime.datetime.now();
			customer.who_modified = user;
			
			m=re.search(r'Ten KH:\s*(.+)',self.request.get('note'));
			if m:customer.name=m.group(1);
			
			m=re.search(r'Dia Chi:\s*(.+)\nSo DT:',self.request.get('note'),re.DOTALL);
			if m:customer.address=db.Text(m.group(1));
			
			m=re.search(r'So DT:\s*(.+)',self.request.get('note'));
			if m:customer.phone=m.group(1);
			
			m=re.search(r'Ngay Sinh Nhat:\s*(\d+)\s*/\s*(\d+)\s*',self.request.get('note'));
			if m:
				customer.birth_day=int(m.group(1));
				customer.birth_month=int(m.group(2));
				
			customer.put();

		#response and redirect
		self.response.out.write(status);
		if(shop):
			if(user):self.redirect('/user/?' + urllib.urlencode({'code': order.code ,'status':status }))
			else:self.redirect('/');
		else:
			self.redirect('/order/?' + urllib.urlencode({'code': order.code ,'status':status,'client':client }))


class ListOrder(webapp.RequestHandler):
	def get(self):
		#Check user
		user=users.get_current_user()
		url_linktext,greeting,user_class=check.check_user(user,self.request.uri);

		if(user_class not in ['manager','employee']):
			#render
			template_values = {
			'greeting': greeting,
			'user_class':user_class,
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
			max=50;
		try:
			page=int(self.request.get('page'));
		except:
			page=0;
		
		#Get sort and filter atribute
		confirm_filter=self.request.get('confirm_filter');
		customer_filter=self.request.get('customer_filter');
		item_filter=self.request.get('item_filter');
		spec_filter=self.request.get('spec_filter');
		show_hidden=self.request.get('show_hidden');


		#Query
		query = db.Query(Order, keys_only=False);
		
		#filter
		if(confirm_filter=='True'):query.filter("confirm =", True);
		elif(confirm_filter=='False'):query.filter("confirm =", False);
		
		if(customer_filter):query.filter("customer =", customer_filter);
		if(item_filter):query.filter("list_item =", item_filter);
		if(spec_filter):query.filter("list_chosen =", spec_filter);
		#default: not show hidden order
		if not show_hidden:query.filter("hidden =", False);
		
		#sort
		query.order('-created');
		
		

		if(max<20):max=20;
		if(page<0):page=0;

		data = query.fetch(max,page*max);

		status="Đây là những đơn hàng từ "+str(page*max)+" tới "+str(page*max+len(data));
		if(len(data)==max):status+=" - Bấm nextpage để xem nhiều hơn!";
		
		#init table
		table=[];
		i=0;
		for order in data:
			#init row
			row=trow();
			row.index=i;
			i+=1;
			#save data to row
			row.code=order.code;
			row.created=order.created;
			row.modified=order.modified;
			row.confirm=order.confirm;
			row.customer=order.customer;
			row.note=order.note;
			#calculate sum of quantity and money
			row.sum_quantity=sum(order.list_quantity);
			row.sum_money=sum( [order.list_price[i]*order.list_quantity[i]for i in range(len(order.list_price))] );

			table+=[row];
		
		
		#save var from request to pass to template
		request=custom();
		request.max=max;request.page=page;
		request.confirm_filter=confirm_filter;
		request.customer_filter=customer_filter;
		request.spec_filter=spec_filter;
		request.item_filter=item_filter;
		request.show_hidden=show_hidden;
		
		#render
		template_values = {
			'greeting': greeting,
			'user_class':user_class,
			'url_linktext': url_linktext,
			'status':status,
			'orders':table,
			'request':request,
		}
		path = os.path.join(os.path.dirname(__file__), 'list_order.html')
		self.response.out.write(template.render(path, template_values))

def main():
	application = webapp.WSGIApplication([
	('/order/', ManageOrder),
	('/order/list/', ListOrder),
	], debug=True)

	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
