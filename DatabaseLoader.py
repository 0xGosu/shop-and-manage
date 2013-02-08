import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
import product

class ProductLoader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Product',
                                   [('code', lambda x: x.decode('utf-8')),
                                    ('created',lambda x: datetime.datetime.strptime(x, '%m/%d/%Y').date()),
                                    ('who_created', lambda x: x.decode('utf-8')),
									('root_price', float),
									('sell_price', float),
									('on_sale', int),
									('quantity', int),
									('category', str),
									('spec_choices', lambda x: x.split(",") ),
									('detail', lambda x: x.decode('utf-8')),
									('photo', str),
                                   ])

loaders = [ProductLoader]