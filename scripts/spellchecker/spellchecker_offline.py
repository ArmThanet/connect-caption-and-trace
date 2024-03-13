import numpy as np
# import requests
# import os,time
import csv

DO_GREEDY_SEARCH = True
cache = "my_TH.csv"

dict_th = [l.rstrip() for l in open('th_TH.dic','r',encoding='utf')]
dict_th.pop(0)
single_char = 'ๆฯ.,()[]<>0123456789-–—๐๑๒๓๔๕๖๗๘๙'
noncheck_char = single_char + 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_:;!?$&\'\"'
dict_ab = [l.split(',')[0] for l in open('ab_TH.dic','r',encoding='utf')]
dict_ab.pop(0)

dict_no = []
dict_en = []
dict_no2en = {}

def addEntry(t):
    if len(t)<2 or t[1]=='':
        return
    dict_en.append(t[1])
    for w in t[2:]:
        if w=='':
            continue
        dict_no.append(w)
        dict_no2en[w] = t[1]
        #remove from TH dic
        if w in dict_th:
            dict_th.remove(w)

with open(cache,'r',encoding='utf') as f:
        spamreader = csv.reader(f, delimiter=',', quotechar='"')
        for l in spamreader:
            addEntry(l)

# for l in open('maybe_TH.csv','r',encoding='utf').readlines():
#     t=l.strip().split(',')
#     dict_en.append(t[1])

langs = ['th','no','en','ab']
dictionary = {'th':dict_th, 'no':dict_no, 'en':dict_en, 'ab':dict_ab}

# '▁'
def spellchecker(input:str, tagged:bool=True)->str:
    dict_cur = {lang:[w for w in dictionary[lang] if w in input] for lang in langs}

    def greedy_search(s_i, e_i):
        candidate = []
        for lang in langs:
            candidate_index = np.nonzero((item[lang][s_i] == s_i))
            candidate += [(len(dict_cur[lang][j]), lang, j) for j in candidate_index[0] if s_i+len(dict_cur[lang][j]) <= e_i]
        candidate.sort(reverse=True)

        for l,lang,j in candidate:
            # if s_i+l > e_i:# or item[lang][s_i,j] != s_i:
            #     continue
            if s_i+l == e_i:
                return [s[s_i:e_i]]
            else:
                greedy_result = greedy_search(s_i+l,e_i)
                if greedy_result is not None:
                    return [s[s_i:s_i+l]] + greedy_result

        return None

    def split_and_remove(offset,lang):    
        w_index = np.nonzero(item[lang][offset] > -1)[0][0]
        offset = item[lang][offset,w_index]
        offset_end = offset+len(dict_cur[lang][w_index])
        cov[lang][offset:offset_end,w_index] = 0 # -= 1
        if any(cov[lang][offset:offset_end,w_index] > 100):
            raise(ValueError)
        item[lang][offset:offset_end,w_index] = -1

        #remove non-complete word
        for lang in langs:
            removed_index = np.nonzero((-1 < item[lang][offset+1:offset_end]) & (item[lang][offset+1:offset_end] <= offset_end))
            for i,j in zip(removed_index[0],removed_index[1]):
                if item[lang][offset+1+i,j] == offset+1+i:
                    l = len(dict_cur[lang][j])
                    cov[lang][offset+1+i:offset+1+i+l,j] = 0 #-= 1
                    if any(cov[lang][offset+1+i:offset+1+i+l,j] > 100):
                        raise(ValueError)
                    item[lang][offset+1+i:offset+1+i+l,j] = -1
        # strm = s[offset:offset_end]
        #return splitsubstr(s_i,offset)+[strm]+splitsubstr(offset_end,e_i)
        return offset,offset_end
    
    def splitsubstr(s_i,e_i):
        if len(s[s_i:e_i])==0:
            return []
        elif len(s[s_i:e_i])==1 and s[s_i:e_i] in single_char:
            return [s[s_i:e_i]]
        
        if s[s_i:e_i] in dict_cur['th']:
            return [s[s_i:e_i]]
        elif s[s_i:e_i] in dict_cur['en']:
            return ['▁en'+s[s_i:e_i]]
        elif s[s_i:e_i] in dict_cur['ab']:
            return ['▁ab'+s[s_i:e_i]]
        elif all([c in noncheck_char for c in s[s_i:e_i]]):
            return [s[s_i:e_i]]
        elif len(s[s_i:e_i])==1:
            return ['▁no'+s[s_i:e_i]]
        
        
        noncov_index = np.nonzero(cov['th'][s_i:e_i].sum(axis=1)==0)[0]
        # noncov_en_index = np.nonzero(cov['en'][s_i:e_i].sum(axis=1)==0)[0]
        if (noncov_index.size > 0):
            #search en & ab dictionary
            for lang in ['en','ab']:
                cov_index = np.nonzero(cov[lang][s_i+noncov_index].sum(axis=1)>0)[0]
                if (cov_index.size > 0):
                    offset = s_i+noncov_index[cov_index[0]]
                    offset,offset_end = split_and_remove(offset,lang)
                    return splitsubstr(s_i,offset)+['▁'+lang+s[offset:offset_end]]+splitsubstr(offset_end,e_i)
                
            #search no dictionary
            cov_index = np.nonzero(cov['no'][s_i+noncov_index].sum(axis=1)>0)[0]
            if (cov_index.size > 0):
                #need to implement MAX for multiple entries
                offset = s_i+noncov_index[cov_index[0]]
                offset,offset_end = split_and_remove(offset,'no')
                strm = s[offset:offset_end]                
                return splitsubstr(s_i,offset)+['▁no'+strm+'▁en'+dict_no2en[strm]]+splitsubstr(offset_end,e_i)
        
            m_i = s_i + noncov_index
            output = []
            for offset in m_i:
                if s_i < offset:
                    output += splitsubstr(s_i,offset)
                #output.append('▁no'+s[offset])
                output.append(splitsubstr(offset,offset+1)[0])
                s_i = offset+1
            output += splitsubstr(s_i,e_i)
            return output
        
        # singular_index = np.nonzero(cov['th'][s_i:e_i].sum(axis=1)==1)[0]
        # singular_index = np.nonzero((cov['th'][s_i:e_i].sum(axis=1)+cov['en'][s_i:e_i].sum(axis=1))==1)[0]
        singular_index = np.nonzero(sum([cov[lang][s_i:e_i].sum(axis=1) for lang in ['th','en','ab']])==1)[0]
        if (singular_index.size == 0):
            if DO_GREEDY_SEARCH:
                greedy_result = greedy_search(s_i,e_i)
                return ['▁no' + s[s_i:e_i]] if greedy_result is None else greedy_result
            else:
                return [s[s_i:e_i]]
        else:
            offset = s_i+singular_index[0]
            # w_index = np.nonzero(item['th'][offset] > -1)[0][0]
            # offset = item['th'][offset,w_index]
            # offset_end = offset+len(dict_cur['th'][w_index])
            # cov['th'][offset:offset_end,w_index] -= 1
            # item['th'][offset:offset_end,w_index] = -1
            # #remove non-complete word
            # removed_index = np.nonzero((-1 < item['th'][offset+1:offset_end]) & (item['th'][offset+1:offset_end] <= offset_end))
            # for i,j in zip(removed_index[0],removed_index[1]):
            #     l = len(dict_cur['th'][j])
            #     cov['th'][offset+1+i:offset+1+i+l,j] -= 1
            #     item['th'][offset+1+i:offset+1+i+l,j] = -1
            # strm = s[offset:offset_end]
            # return splitsubstr(s_i,offset)+[strm]+splitsubstr(offset_end,e_i)
            offset,offset_end = split_and_remove(offset,'th')
            return splitsubstr(s_i,offset)+[s[offset:offset_end]]+splitsubstr(offset_end,e_i)

    strs = input.split(' ')
    output = []
    for i in range(len(strs)):
        s = strs[i]
        if(len(s) == 1):
            output.append([s])
        else:
            cov = {lang:np.zeros((len(s),len(dict_cur[lang])), dtype='u4') for lang in langs}
            item = {lang:-np.ones((len(s),len(dict_cur[lang])), dtype='i4') for lang in langs}
            for lang in langs:
                for j,w in enumerate(dict_cur[lang]):
                    offset = 0
                    while True:
                        try:
                            offset = s.index(w, offset)
                        except ValueError:
                            break
                        cov[lang][offset:offset+len(w),j] += 1
                        item[lang][offset:offset+len(w),j] = offset
                        offset += len(w)
                    # print(f'{w} : {input.index(w)}')
            output.append(splitsubstr(0,len(s)))
    return output#' '.join(output)  

# def tohtml(spelledchecked:list):
#     output = []
#     for row in spelledchecked:
#         marked = False
#         for j in range(len(row)):
#             if row[j][0] == '▁':
#                 row[j] = ('' if marked else '<mark>[') + row[j][1:]
#                 marked = True
#             elif marked:
#                 row[j-1] += ']</mark>'
#                 marked = False
#         if marked:
#             row[-1] += ']</mark>'
#         output.append('·'.join(row))
#     return ' '.join(output)
def log_tohtml(s:str,i:int)->str:
    n = len(s)
    context = ''.join(s[min(n,i+1):min(n,i+3)])

    output = s[i]
    while not s[i].startswith('<mark>['):
        i-=1
        output = s[i]+output
    output = output[7:-8]

    context = ''.join(s[max(0,i-2):max(0,i)]) + output + context

    with open('log_tohtml.txt','a') as f:
        f.writelines(f'{output}\t{context}\n')

def tokenize(input:str):
    output = None
    for row in spellchecker(input, tagged=False):
        for j in range(len(row)):
            if row[j].startswith('▁no'):
                if '▁en' in row[j]:
                    rows = row[j].split('▁en')
                    row[j] = rows[1]
                elif row[j][3:] == '\u200b':
                    row[j] = ''
                else:
                    row[j] = row[j][3:]
            elif row[j].startswith('▁en') or row[j].startswith('▁ab'):
                row[j] = row[j][3:]

        if output:
            output += [' '] + row
        else:
            output = row
    return output

def tohtml(spelledchecked:list, log=True):
    output = []
    for row in spelledchecked:
        marked = False
        for j in range(len(row)):
            if row[j].startswith('▁no'):
                if '▁en' in row[j]:
                    rows = row[j].split('▁en')
                    row[j] = '<mark>[<s>' + rows[0][3:] + '</s> → ทับศัพท์:' + rows[1] + ']</mark>'
                else:
                    if row[j][3:] == '\u200b':
                        row[j] = '▁no[ZWSP]'
                    row[j] = ('' if marked else '<mark>[') + row[j][3:]
                    marked = True
            elif marked:
                row[j-1] += ']</mark>'
                if log:
                    log_tohtml(row,j-1)
                marked = False
                
            if row[j].startswith('▁en'):
                row[j] = '[ทับศัพท์:' + row[j][3:] +']'

            if row[j].startswith('▁ab'):
                row[j] = '[ตัวย่อ:' + row[j][3:] +']'
        if marked:
            row[-1] += ']</mark>'
            if log:
                log_tohtml(row,-1)

        output.append('·'.join(row))
    return ' '.join(output)

if __name__ == '__main__':
    texts = [
        "ผู้ชายผิวขาวผมสีน้ำตาลสวมเสื้อเว็ตสูทสีดำกำลังถือเซิร์ฟบอร์ด",
        "Microsoft Paint เตรียมอัปเดตใหม่ แบ่งเลเยอร์ได้ ซ้อนภาพพื้นหลังโปร่งใสได้เหมือน Photoshop",
        "เครื่องบินโดยสารมีตัวอักษรสีเทาตัวใหญ่ด้านข้าง เครื่องสีดำมีใบพัด 2 ข้างและมีบันไดพาดด้านซ้าย",
        "ภาพถ่ายขาวดำของร้านค้าที่ตกแต่งและให้บรรยากาศคล้ายย้อนยุคไปเมื่อ 100 ปีก่อน",
        "ผู้ชายผมสั้นสีดำสวมเสื้อแขนยาวสีขาวกางเกงขายาวกำลังเล่นสเก็ตบอร์ด",
        "ผู้ชายผมสั้นสีดำสวมเสื้อแขนยาวสีขาวกางเกงขายาวกำลังเล่นเนคไทสเก๊ตบอร์ด",
        "ห้องทาผนังสีขาวและสีน้ำตาล มีโซฟาไม้วางเบาะสีขาวพร้อมหมอนสีขาวและแดง โดยด้านข้างเป็นโต๊ะวางของสีแดงที่มีตระกร้าผลไม้และกระถางต้นไม้ตั้งอยู่",
        "ผู้ชายสวมชุุดหมีสีฟ้ายืนกดโทรศัพท์อยู่ข้างรถฟู้ดทรักสีขาว มีคนกำลังยืนต่อคิวซื้ออาหาร",
        "ผู้หญิงสวมเสื้อสีแดงยืนถือจอยสติกสีขาว อยู่ข้างผู้ชายสวมเสื้อสีเขียวใส่แว่น",
        "หญิงใส่เสื้อสีดำกางเกงสีขาวถือร่มสีดำยืนอยู่ด้านข้างของผู้หญิงสวมเสื้อสีขาวกางเกงสีเข้มอยู่บนฟุตบาทด้านข้างมีคนยืนคล่อมจักรยานและมีคนเดินอยู่จำนวนมากด้านหลังเป็นนอาคารและตึก",
        "กล่องอาหารสีเขียว ใส่แฮมสีชมพู แครอท บล็อกโคลี่ มะเขือเทศ สตรอเบอรี่ ส้ม",
        "เรือจอดอยู่ด้านข้างสีเเดงลายดอกไม้ ด้านบนบรรทุกรถเมล์สีขาวฟ้า",
        "ผู้คนจำนวนมากเล่นไคต์บอร์ด อยู่ในทะเล โดยลอยเหนือคลื่นสีขาวที่ม้วนเป็นเกลียวอยู่ด้านล่าง",
        "นาฬิกาเข็มสองตัวบนปราสาทโบราณ บอกเวลา 17.13 น. ด้านหลังมีดวงจันทร์",
        "ต้นกันเกราต้นหนึ่ง ทรงปลูกโดยสมเด็จพระเทพรัตนราชสุดาฯ สยามบรมราชกุมารี(พระเทพ)  ที่โคนต้นมีพุ่มต้นเข็มดอกสีแดงปลูกล้อมรอบเป็นวงกลม",
        "บ้านขนาดเล็กที่ผนังด้านข้างทำจากไม้สีน้ำตาลท่อนเล็กเรียงต่อกัน โครงของบ้านทำด้วยเหล็กสีขาวและมีระเบียงยื่นออกมาด้านขวา หลังคาของบ้านทำจากสังกะสีสีเขียวอ่อน ด้านซ้ายของตัวบ้านมีหน้าต่างบานเกล็ด ด้านขวาของตัวบ้านฝั่งเดียวกับระเบียงที่ยื่นออกมามีประตูไม้สีน้ำตาล บริเวณรอบบ้านมีต้นไม้สีเขียวขึ้นอยู่จำนวนมาก",
        "สังกะสีสีเขียว", #double adjacent word bug
        "ข้าวเกรียบหั่นเป็นวงกลมทอดสีเหลืองจำนวนหลายชิ้นวางอยู่ในถาด และไส้กรอกผ่านการทอดจนสุกวางอยู่",
        "โทรศัพท์สีดำพร้อมอุปกรณ์วางอยู่ในกล่องโทรศัพท์พร้อมคู่มือ",
        "อาหารประเภทขนมปังและเฟรนช์ฟรายส์วางอยู่ในจานสีขาวขอบจานเป็นลวดลายส้อมวางอยู่ทางซ้าย",
        "คนเล่นไคต์เซิร์ฟสีแดงที่มีลวดลายสีดำใหญ่อยู่กลางทะเลกว้างโดยมีทิวทัศน์ภูเขาอยู่ด้านนอก",
        "รถยนต์สีเหลือง​ ด้านหน้ารถแซมด้วยสีม่วง​ด้านข้างรถมีป้ายสีเหลี่ยมพื้นสีแดงตัวอักษรสีขาวอยู่ด้านหน้ารถยนต์สีขาวคันใหญ่"
        "คนหลายคนกำลังเดินอยู่ในสนามหญ้า ว่าวหลายตัวลอยอยู่บนท้องฟ้า",
        "แผ่นป้ายบอกชื่อสถานที่เขียนว่า 17 AVE S ติดอยู่บนเสา ข้างกับป้ายที่เขียนว่า Stevens St",
        "ผู้ชายสวมแว่นกันแดดสีดำสวมเสื้อสีม่วงนั่งกินสปาเกตตีในร้านอาหาร มีแก้วน้ำวางอยู่ด้านหน้า",
        "บนโต๊ะไม้มีแจกกันใส่ดอกไม้สีชมพู ข้างๆมีแก้ว มีเลม่อน มีไวท์ ด้านหลังมีเครื่องทำกาแฟและตู้เย็น",
        "โดนัทหลายกล่องวางอยู่บนโต๊ะ โดยมีคนยืนอยู่ล้อมรอบ",
        "ป้ายวงกลมสีขาวตัวอักษร ว แหวน สีเทาติดอยู่บนเสาสีขาวขึ้นสนิม"]
    for t in texts:
        # o = spellchecker(t)
        # print(o)
        # print(tohtml(o))
        print(tokenize(t))


    # print(tokenize("ป้ายวงกลมสีขาวตัวอักษร ว แหวน สีเทาติดอยู่บนเสาสีขาวขึ้นสนิม"))
    pass