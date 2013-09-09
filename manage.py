#!/usr/bin/env python
import os
import sys
import json
import csv
import re
from datetime import datetime,timedelta

def clearItems(store):
  Item.objects.filter(store__name__icontains=store).delete()
  Store.objects.filter(name__icontains=store).delete()

def _getAllCsvFiles(folder):
  res = []
  for f in os.listdir(folder):
    if f.endswith('.csv'):
      res.append(folder + f)
    elif os.path.isdir(folder + f):
      res.extend(_getAllCsvFiles(folder + f + os.path.sep))
  return res

def showOrders():
  for o in Order.objects.all():
    print o

def trim(s):
  return re.sub('(^\s+|\s+$)', '', s)


def loadBookstoreItems():
  bookstore = Store(name = 'bookstore', address = "")
  bookstore.save()
  items = []
  for fname in _getAllCsvFiles('data/bookstore/'):
    f = csv.reader(open(fname))
    next(f) # eat the header 
    print fname
    for lst in f:
      items.append((map(trim, lst), fname))
  DPT=0
  CRS=1
  SECTION=2
  E_EN=3
  PROV=4
  RO=5
  AUTHOR=6
  TITLE=7
  VL=8
  ED=9
  PUBLISHER=10
  CP=11
  B=12
  PRICE=13
  CATEGORY=14
  PIC=15
  TAX_STATUS=16
  TAX_CLASS=17
  OUT_OF_STOCK=19

  def getRemark(item):
    res = {}
    if item[DPT]:
      res["dpt"] = item[DPT]
    if item[CRS]:
      res["crs"] = item[CRS]
    if item[SECTION]:
      res["section"] = item[SECTION]
    if item[E_EN]:
      res["e/en"] = item[E_EN]
    if item[PROV]:
      res["prov"] = item[PROV]
    if item[RO]:
      res["r/o"] = item[RO]
    if item[AUTHOR]:
      res["author"] = item[AUTHOR]
    if item[VL]:
      res["vl"] = item[VL]
    if item[ED]:
      res["ed"] = item[ED]
    if item[PUBLISHER]:
      res["publisher"] = item[PUBLISHER]
    if item[CP]:
      res["cp"] = item[CP]
    if item[B]:
      res["b"] = item[B]
    if item[PIC]:
      res["pic"] = item[PIC]
    return json.dumps(res)

  print "%d books to write" % len(items)
  ct = 0
  addedBooks = set()
  problemFiles = set()
  for item,fname in items:
    try:
      bookid = (item[TITLE], item[AUTHOR], item[ED], item[PRICE], item[DPT], item[CRS])
      if bookid in addedBooks: continue
      addedBooks.add(bookid)
      if item[CATEGORY] and item[TITLE] and item[PRICE] \
          and item[TAX_STATUS] and item[TAX_CLASS]:
        Item(store = bookstore, category = item[CATEGORY],
            name = item[TITLE], price = item[PRICE],
            sku = os.path.splitext(item[PIC])[0],
            out_of_stock = (item[OUT_OF_STOCK] == '*'),
            tax_status = item[TAX_STATUS], tax_class = item[TAX_CLASS],
            remark = getRemark(item)).save()
      else:
        if fname in problemFiles:
          continue
        else:
          problemFiles.add(fname)
          print 'data in %s is not complete' % fname
          print item
    except Exception as e:
      print e, fname, item
    ct += 1
    if ct%100==0:
      print "%d books written" % ct

def loadSobeysItems():
  sobeys = Store(name = 'sobeys', address = "450 Columbia St W, Waterloo ON N2T 2W1")
  sobeys.save()
  items = []
  for fname in _getAllCsvFiles('data/sobeys/'):
    f = csv.reader(open(fname))
    next(f) # eat the header 
    print fname
    for lst in f:
      items.append((map(trim, lst), fname))
  TITLE=0
  CATEGORY=3
  PRICE=5
  SALES_PRICE=7
  WEIGHT=8
  LENGTH=9
  WIDTH=10
  HEIGHT=11
  SKU=12
  TAX_STATUS=15
  TAX_CLASS=16

  def getRemark(item):
    res = {}
    if item[WEIGHT]:
      res["weight"] = item[WEIGHT]
    if item[LENGTH]:
      res["length"] = item[LENGTH]
    if item[WIDTH]:
      res["width"] = item[WIDTH]
    if item[HEIGHT]:
      res["height"] = item[HEIGHT]
    if item[SALES_PRICE]:
      res["sales_price"] = item[SALES_PRICE]
    return json.dumps(res)

  print "%d items to write" % len(items)
  ct = 0
  problemFiles = set()
  for item,fname in items:
    try:
      if item[CATEGORY] and item[TITLE] and item[SKU] and item[PRICE] \
          and item[TAX_STATUS] and item[TAX_CLASS]:
        Item(store = sobeys, category = item[CATEGORY],
            name = item[TITLE], price = item[PRICE], sku = item[SKU],
            tax_status = item[TAX_STATUS], tax_class = item[TAX_CLASS],
            remark = getRemark(item)).save()
      else:
        if fname in problemFiles:
          continue
        else:
          problemFiles.add(fname)
          print 'data in %s is not complete' % fname
          print item
    except Exception as e:
      print e, fname, item
    ct += 1
    if ct%100==0:
      print "%d items written" % ct

def fetchCategory(store):
  res = set()
  for it in Item.objects.filter(store__name__icontains=store):
    res.add(it.category)
  for c in res:
    print c

def showTax():
  tax={}
  for o in Item.objects.all():
    s = o.tax_class
    if s in tax:
      tax[s]+=1
    else:
      tax[s] = 1
  print tax

def fixTypo():
  ct = 0
  for o in Item.objects.all():
    if 'Goceries' in  o.category:
      o.category = o.category.replace('Goceries', 'Groceries')
      o.save()
      ct += 1
  print '%d items fixed' % ct

def initItemSoldNumber():
  ct = {}
  for o in Order.objects.exclude(status='pending'):
    l = json.loads(o.items)
    for i in l:
      if i not in ct:
        ct[i] = 1
      else:
        ct[i] += 1
  for item in Item.objects.all():
    if item.id in ct:
      item.sold_number = ct[item.id]
    else:
      item.sold_number = 0
    item.save()

def clearOrder():
  Order.objects.filter(status='pending').filter(time__lt=datetime.now() - timedelta(minutes=1)).delete()

def showVersion():
  import django
  print django.VERSION

def testMail():
  from cart.models import send_receipt
  send_receipt('biran0079@gmail.com', 'test mail', 'test msg')

def checkImg(store):
  for it in Item.objects.filter(store__name=store).exclude(out_of_stock=1):
    imgf = '/fruitex-imgs/%s_imgs/%s' % (store,  it.sku + '.JPG')
    if not os.path.exists(imgf):
      print 'Missing image for item: %d' % it.id

def main(argv):
  def _arg(i):
    if len(argv) > i:
      return argv[i]
    return ''

  if _arg(1) == 'clear':
    clearItems(_arg(2))
  elif _arg(1) == 'load':
    loadSobeysItems()
    loadBookstoreItems()
  elif _arg(1) == 'cate':
    fetchCategory(_arg(2))
  elif _arg(1) == 'order':
    showOrders()
  elif _arg(1) == 'tax':
    showTax()
  elif _arg(1) == 'fix':
    fixTypo()
  elif _arg(1) == 'init_sold_num':
    initItemSoldNumber()
  elif _arg(1) == 'v':
    showVersion()
  elif _arg(1) == 'clear_pending_orders':
    clearOrder()
  elif _arg(1) == 'test_mail':
    testMail()
  elif _arg(1) == 'check_img':
    checkImg(_arg(2))
  else:
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fruitex.settings")
  from home.models import Store, Item
  from cart.models import Order
  main(sys.argv)

