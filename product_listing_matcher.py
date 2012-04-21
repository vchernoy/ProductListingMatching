# Author: Chernoy Viacheslav
# email: vchenoy@gmail.com

# The program matches product listings from a 3rd party retailer.
# Problem is presented by Sortable
# http://sortable.com/blog/coding-challenge

import json, math, operator

DEBUG = False

CURRENCY_EXCH = {'usd':1., 'eur':1.30781, 'gbp':1.58827, 'cad':1.00209, 'aud':1.03697, 'jpy':0.0123550, 'chf':1.08817, 'nzd':0.826091}

REPLACING_WORDS = [('mega pixels', 'mpix'), ('mega-pixels', 'mpix'), ('megapixels',  'mpix'), ('mega pixel',  'mpix'), 
                   ('mega-pixel',  'mpix'), ('megapixel',   'mpix'), ('mega pix',    'mpix'), ('mega-pix',    'mpix'), 
                   ('megapix',     'mpix'), ('Mpixels',     'mpix'), ('mpix',        'Mpix'), ('mp',          'mpix'),
                   ('Mpix',        'mpix'), (' mpix',       'mpix'), ('w/', 'with ')]

def log(msg):
    global DEBUG

    if DEBUG:
        print msg

def word_cleared_str(s):
    for t in REPLACING_WORDS:
        s = s.replace(t[0], t[1])

    return s

def tokenize(l0):
    l1 = []
    for w in l0:
        l1.extend(word_cleared_str(w).split())

    separators = '-:_|()'
    for sep in separators:
        l = []
        for w in l1:
            l.extend(w.split(sep))
        l1 = l

    s = set(l)
    s.difference(set(['', '-', ':', '_', '|', '(', ')', 'with', 'and', '&']))

    l = [x for x in s]
    l.sort()

    return l

def norm(s):
    return s.lower().strip()

def sep_cleared_str(s):
    seps = ',._-:/\\|'
    return ''.join(''.join([' ' if c in seps else c for c in s]).split())

class Product:
    def __init__(self, model, date, name, manufacturer, family):
        self.name         = norm(name)
        self.model        = norm(model)
        self.date         = norm(date)
        self.manufacturer = norm(manufacturer)
        self.family       = norm(family)

        self.name = self.name.replace(self.manufacturer, '')
        self.manufacturer = sep_cleared_str(self.manufacturer)
        for w in self.manufacturer.split():
            self.name = self.name.replace(w, '')

        self.name = self.name.strip(',._-:/\\|')

        self.tokenize()
        self.listings = []
        self.min_price = self.max_price = self.k = None

        self.orig_name         = name
        self.orig_model        = model
        self.orig_date         = date
        self.orig_manufacturer = manufacturer
        self.orig_family       = family

    def tokenize(self):
        self.tokens = tokenize([self.name, self.model, self.family])

    def update_price(self, k=1.):
        self.min_price = self.max_price = None
        self.k = k
        if len(self.listings) > 0:
            price_sum = sum([l.price for l in self.listings])
            sq_price_sum = sum([l.price**2 for l in self.listings])
            mean = price_sum / len(self.listings)
            var = math.sqrt(sq_price_sum / len(self.listings) - mean**2) if len(self.listings) > 1 else mean / 3.
            var = max(var, mean*0.3) 
            self.max_price = mean + var*k
            self.min_price = mean - var*k*mean / (mean + var*k)

    def matches_price(self, price):
        saved_listings = self.listings[:]
        self.listings = [l for l in self.listings if l.price != price]
        if len(self.listings) >= 2:
            self.update_price(self.k)
            matches = (self.max_price == None) or ((price >= self.min_price) and (price <= self.max_price))
        else:
            matches = True
            
        self.listings = saved_listings

        return matches

    def __str__(self):
        l = [self.name, ', ', self.model, ', ', self.family, ', ', self.manufacturer]
        if self.max_price:
            l.extends([', ', str(int(self.min_price)), '..', str(int(self.max_price))])

        return ''.join(l)

def as_product(d):
    return Product(d['model'], d['announced-date'], d['product_name'], d['manufacturer'], d.get('family', ''))

class Listing:
    def __init__(self, title, manufacturer, currency, price):
        self.title        = norm(title)
        self.manufacturer = norm(manufacturer)
        self.currency     = norm(currency)
        self.price        = CURRENCY_EXCH[self.currency] * float(norm(price))

        self.title = self.title.replace(self.manufacturer, '')
        self.manufacturer = sep_cleared_str(self.manufacturer)
        for w in self.manufacturer.split():
            self.title = self.title.replace(w, '')

        self.title = word_cleared_str(self.title.strip(',._-:/\\| '))

        self.tokenize()

        self.orig_title        = title
        self.orig_manufacturer = manufacturer
        self.orig_currency     = currency
        self.orig_price        = price

    def tokenize(self):
        self.tokens = tokenize([self.title, self.title.replace('-', '')])

    def __str__(self):
        return repr(self.title) + repr(', ' + self.manufacturer + ', ' + str(int(self.price)))

def as_listing(d):
    return Listing(d['title'], d['manufacturer'], d['currency'], d['price'])

def matched(tokens, tokens2):
    for w in tokens:
        if w not in tokens2:
            ok = False 
            for z in tokens2:
                if z.startswith(w):
                    for u in tokens:
                        if w + u == z:
                            ok = True
                            break
                elif z.endswith(w):
                    for u in tokens:
                        if u + w == z:
                            ok = True
                            break

            if not ok:  
                return False

    return True

def matched_strongly(tokens, tokens2):
    for w in tokens:
        if w not in tokens2:
            return False

    return True

def matched_start_or_end(tokens, tokens2):
    for w in tokens:
        if not [z for z in tokens2 if z.startswith(w) or z.endswith(w)]:
            return False

    return True

def matched_substr(tokens, tokens2):
    for w in tokens:
        if not [z for z in tokens2 if w in z]:
            return False

    return True

def format(d):
    return ', '.join(sorted(d.keys()))

products = {}
with open('products.txt', 'r') as f:
    for s in f:
        p = json.loads(s, object_hook=as_product)

        if not [p1 for p1 in products.get(p.manufacturer, []) \
                if (p.name == p1.name) or ((p.date == p1.date) and matched(p.tokens, p1.tokens) and matched(p1.tokens, p.tokens))]:
            products.setdefault(p.manufacturer, []).append(p)
        else:
            log('Ignoring: ' + str(p))

manufactures = products.keys()
listings = []
with open('listings.txt', 'r') as f:
    for s in f:
        l = json.loads(s, object_hook=as_listing)
        if [m for m in manufactures if m in l.manufacturer]:
            listings.append(l)
        else:
            log('Ignoring: ' + str(l))

for l in listings:
    l.matched_products = [p for m in manufactures if m in l.manufacturer for p in products[m] if matched(p.tokens, l.tokens)]
    if len(l.matched_products) == 1:
        l.matched_products[0].listings.append(l)

for m in manufactures:
    for p in products[m]:
        p.update_price(1.5)

for l in listings:
    if len(l.matched_products) > 1:
        matching_price_products = [p for p in l.matched_products if p.matches_price(l.price)]
        if len(matching_price_products) == 1:
            p = matching_price_products[0]
            p.listings.append(l)
            l.matched_products.remove(p)
            l.matched_products.insert(0, p)
        elif len(matching_price_products) >= 2:
            max_no_toks = max([len(p.tokens) for p in matching_price_products])
            max_lo_toks = max([len(''.join(p.tokens)) for p in matching_price_products])
            matching_price_products2 = [p for p in matching_price_products if (len(p.tokens) == max_no_toks) and (len(''.join(p.tokens)) == max_lo_toks)] 
            if len(matching_price_products2) == 1:
                p = matching_price_products2[0]
                p.listings.append(l)

for m in manufactures:
    for p in products[m]:
        p.update_price(7.)
        unmatched_listings = [l for l in p.listings if not p.matches_price(l.price)]
        if unmatched_listings:
            matched_listings = [l for l in p.listings if l not in unmatched_listings]
            similar_to_matched_listings = [l for l in unmatched_listings if [l2 for l2 in matched_listings if matched(l.tokens, l2.tokens)]]
            for l in unmatched_listings:
                if l not in similar_to_matched_listings:
                    p.listings.remove(l)

for m in sorted(products.keys()):
    for p in sorted(products[m], key=operator.attrgetter('name')):
        if p.listings:
            obj = {'product_name':p.orig_name}
            if not DEBUG:
                listings = obj.setdefault('listings', [])

            for l in sorted(p.listings, key=operator.attrgetter('title')):
                log(p.orig_name + ', ' + p.orig_manufacturer + ': ' + str(l))
                if not DEBUG:
                    listings.append({'title':l.orig_title, 'manufacturer':l.orig_manufacturer, 'currency':l.orig_currency, 'price':l.orig_price})

            if not DEBUG:
                print json.dumps(obj)
            

