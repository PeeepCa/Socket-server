import socketserver
import cx_Oracle as ora
import time
import socket 

array = {}
version = '0.6'

#Ver 0.3    - Added new function called compName - can be used for binning
#Ver 0.4    - Fixed issue with empty response string (Fixed by clearing array after the comman)
#           - Added response fail code to "bom" function
#           - Added "help" function
#Ver 0.5    - Rebuilding function handler and separating it to different class and function(Probably faster solution)
#           - Added response timer (server now displays also response timer so you should see how long it takes server to responde)
#Ver 0.6    - Server Address added to the config

class misc:
    def readConfig():
        file = open('config.ini', 'r')
        temp = file.readlines()
        port = temp[1].split('=')
        port = port[1]
        port = port.replace('\n','')
        address = temp[0].split('=')
        address = address[1]
        address = address.replace('\n','')
        file.close()
        return address, port

class IFS:
    def login():
        conn_str = ##u'' server login and adress
        conn = ora.connect(conn_str)
        return conn
    def bom(conn , wa , comp):
        wa = wa.replace('WA','')
        x = 0
        c = conn.cursor()
        c.execute(""" select
               a.part_no,
               a.draw_pos_no,
               a.condition_code
                
               from ifsapp.shop_material_alloc a 
               where a.order_no = '""" + wa + """' 
                     and draw_pos_no like '""" + comp + """' """)
        for row in c:
            row = str(row)
            array[x] = row
            x = x + 1
        return array

    def compName(conn , wa , comp):
        wa = wa.replace('WA','')
        x = 0
        c = conn.cursor()
        c.execute(""" select
               a.draw_pos_no
                
               from ifsapp.shop_material_alloc a 
               where a.order_no = '""" + wa + """' 
                     and draw_pos_no like '""" + comp + """' """)
        for row in c:
            row = str(row)
            array[x] = row
            x = x + 1
        return array
    def binning(conn , wa):
        wa = wa.replace('WA','')
        x = 0
        c = conn.cursor()
        c.execute(""" select a.order_no,
               a.draw_pos_no || ';' ||  ifsapp.part_catalog_api.Get_Description(a.part_no) || ';' as description,
               a.line_item_no,
               a.part_no,
               a.draw_pos_no,
               a.condition_code,
               a.note_text,
               ifsapp.part_catalog_api.Get_Description(a.part_no),
               a.qty_per_assembly,
               a.operation_no,
               a.structure_line_no,
               a.date_required,
               a.last_issue_date 
                
               from ifsapp.shop_material_alloc a 
               where a.order_no = '""" + wa + """'""")
        for row in c:
            row = str(row)
            array[x] = row
            x = x + 1
        return array
    def logout(conn):
        conn.close()

class mainHandler:
    def mainFunction(dataRec):
        print(dataRec)
        dataf = ''
        if b'help' in dataRec:
            if b'bom' in dataRec:
                dataProc = b'bom,WAxxxxxx,% - % can be replaced with component name'
            elif b'compName' in dataRec:
                dataProc = b'compName,WAxxxxxx,% - % can be replaced with component name'
            elif b'ping' in dataRec:
                dataProc = b'If is server alive it should reply "pong"'
            else:
                dataProc = b'Commands : bom , compName , ping'
        elif b'ping' in dataRec:
            dataProc = b'pong'
            array.clear()
        elif b'bom' in dataRec:
            wa = str(dataRec)
            wa = wa.split(',')
            comp = wa[2].replace("'",'')
            wa = wa[1].replace("'",'')
            conn = IFS.login()
            array = IFS.bom(conn,wa,comp)
            IFS.logout(conn)
            for x in array:
                data = array[x]
                data = data[1:-1]
                data = data.replace("'",'')
                data = data.replace('None','')
                data = data.replace(', ',',')
                if x == 0:
                    dataf = dataf + data
                else:
                    dataf = dataf + ',' + data
            if not dataf:
                status = b'1'
            else:
                status = b'0'
            dataProc = status + b',' + dataf.encode() + b'$'
            array.clear()
        elif b'compName' in dataRec:
            wa = str(dataRec)
            wa = wa.split(',')
            comp = wa[2].replace("'",'')
            wa = wa[1].replace("'",'')
            conn = IFS.login()
            array = IFS.compName(conn,wa,comp)
            IFS.logout(conn)
            for x in array:
                data = array[x]
                data = data[1:-1]
                data = data.replace("'",'')
                data = data.replace('None','')
                data = data.replace(', ',',')
                dataf = dataf + data
            dataProc = status + b',' + dataf.encode() + b'$'
            array.clear()
        else:
            dataProc = b'Unknown command: ' + dataRec
        return dataProc
        
class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        t0 = time.time()
        self.data = self.request.recv(1024).strip()
        time.sleep(0.01)
        print (b'Received: ' + self.data + b' from: ' + self.client_address[0].encode())
        dataRec = mainHandler.mainFunction(self.data)
        self.request.sendall(dataRec)
        t1 = time.time()
        print('Data sent back to: ' + self.client_address[0] + ' in ' +str(t1-t0)[:5] + 'ms')

if __name__ == '__main__':    
    try:
        temp = misc.readConfig()
        serverAddress = temp[0]
        serverPort = temp[1]
        HOST, PORT = serverAddress, int(serverPort)
        server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
        print('Server started as: ' + str(HOST) + ':' + str(PORT))
        print('Server version:' + version)
        print('')
        print('For available commands please send command "help"')
        print('Every command alse have help just write "command help"')
        print('')
        server.serve_forever()
    except:
        if KeyboardInterrupt:
            print('Application stopped by user')
            server.shutdown()
        else:
            print('Application crashed')
