import re

#valid mail address ex: tranvietanh1991@gmail.com
mail = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')


#reply an user ex: @tranvietanh1991
reply = re.compile(r'@[\w\-]+[a-zA-Z0-9]{1,4}')
