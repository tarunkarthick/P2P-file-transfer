import socket
import sys
import threading
import pickle
import traceback
import re
import queue

max_chunk=1024

class peer:
    def __init__(self,host,port,no_of_connections):
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host#ip address of the server
        self.port=port#portno of the server
        print("\n")
        print(self.host,":",self.port)
        self.no_of_connections=no_of_connections#maximum no.of.connections

        try:
            self.s.connect((self.host,self.port))
            #trying for connection with the server
        except(ConnectionRefusedError):
            print("Failed to establish connetion with server\n")
            sys.exit()
        except(TimeoutError):
            print('\npeer not responding connection failed\n')
            sys.exit()
        else:
            #receiving peerid and port of the peer
            a=self.s.recv(max_chunk)
            a=pickle.loads(a)
            print("\nConnection Established:\nPeer_ID:",a[0])
            self.peerport=a[1]#port available for this peer machine



    def download(self,addr,file_name):
        try:
            #downloading the file
            #creating a client mode
            self.s2=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.s2.connect(addr)
            self.s2.send(pickle.dumps(file_name))
            a=pickle.loads(self.s2.recv(max_chunk))
            var=False
            if(a=='filefound'):
                print("filefound")
                self.s2.send(pickle.dumps('send'))
                #opening the output file
                file=open(file_name,'wb')
                txt='sent'
                data=self.s2.recv(max_chunk)
                #writing into the file
                while True:
                        file.write(data)
                        data=self.s2.recv(max_chunk)
                        a=re.findall(txt,str(data))
                        if(a):
                            break
                file.close()
                self.s2.send(pickle.dumps('received'))
                var=True
            elif(a=='filenotfound'):
                var=False
                self.s2.close()
        except(ConnectionRefusedError):
            print("\nConnection not able to establish with server\n")
            var=False
        except(TimeoutError):
            print("\npeer not responding connection failed")
            var=False
        return var


    def sendfile(self,client,addr,que):
        try:
            print("Preparing for sending to peer")
            #sending the file from the peer
            #containing it
            file_name=client.recv(max_chunk)
            file_name=pickle.loads(file_name)
            f=open(file_name,'rb')
            msg='filefound'
            client.send(pickle.dumps(msg))
            acknowledge=pickle.loads(client.recv(max_chunk))
            if(acknowledge=='send'):
                #reading the file
                #reading max_chunk from file
                a=f.read(max_chunk)
                while(a):
                    client.send(a)
                    a=f.read(max_chunk)
                f.close()
                client.send(pickle.dumps('sent'))
                data=pickle.loads(client.recv(max_chunk))
                #if reply is received file is sent
                if(data=='received'):
                    print(file_name+' sent')
                    client.close()
        except(FileNotFoundError):
            a="Filenotfound"
            client.send(pickle.dumps(a))
            que.put(False)
        except:
            print("File transfer failed")
            que.put(False)
        else:
            que.put('okay')


    def search(self,file_name):
        #searching for the file in the centralized directory
        self.s.send(pickle.dumps('search'))
        a=False
        reply=self.s.recv(max_chunk)
        #reply from directory
        if(pickle.loads(reply)=='ok'):
            self.s.send(pickle.dumps(file_name))
            data=self.s.recv(max_chunk)
            data=pickle.loads(data)
            if(data=='found'):
                #asking for downloading the file
                proceed=input("\nFile Found\nProceed further to download(y/n)\n")
                if(proceed=='y'):
                    self.s.send(pickle.dumps('send'))
                    data=self.s.recv(max_chunk)
                    data=pickle.loads(data)
                    if(len(data)==1):
                        #only one peer contains the file
                        self.s.send(pickle.dumps(data[0]))
                    else:
                        #In case of many peers
                        #from which peer file should be extracted 
                        #must be specified
                        print("select the peer from which the file can be extracted\n")
                        for i in range(len(data)):
                            print(i+1,"-> ",data[i])
                        choice=int(input("Enter the choice of the peer:\n"))
                        self.s.send(pickle.dumps(data[choice-1]))
                    print("Sending the address of the peer having file")
                    addr=pickle.loads(self.s.recv(max_chunk))
                    a=self.download(addr,file_name)
                elif(proceed=='n'):
                    self.s.send(pickle.dumps('n'))
                    a='sch'#only search successful
            elif(data=='not found'):
                print("File not found with any peer\n")
                a=False
        return a


    def seed(self):
        try:
            #making the peer for seeding
            self.s1=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.host1=socket.gethostbyname(socket.gethostname())#host of the peer
            self.s1.bind((self.host1,self.peerport))
            self.s1.listen(self.no_of_connections)

            while True:
                 #accepting clients
                client,addr=self.s1.accept()
                print("Connected with "+str(addr[0]),":",addr[1])

                try:
                    que=queue.Queue()
                    #creating of threads for peers individually
                    t=threading.Thread(target=self.sendfile,args=(client,addr,que))
                    t.start()
                    var=que.get()
                    self.s1.close()
                    return var
                except:
                    print("Thread did not start")
                    #tracing back to normal state without halting
                    traceback.print_exc()
        except(KeyboardInterrupt):
            print("seeding stopped")
        return True


    def register(self,file_name):
        #for registering the file
        self.s.send(pickle.dumps('register'))
        reply=pickle.loads(self.s.recv(max_chunk))
        #asking for reply
        if(reply=='ok'):
            self.s.send(pickle.dumps(file_name))
            reply=pickle.loads(self.s.recv(max_chunk))
            if(reply=='success'):
                #asking for seeding 
                #conformation is acknowledged
                proceed=input("File registered.\nproceed to seed(y/n)\n")
                if(proceed=='y'):
                    print("seeding mode\n")
                    var=self.seed()
                    return var
                else:
                    return True
            else:
                return False
        else:
            return False


    def quit(self):
        self.s.send(pickle.dumps('bye'))
        if(pickle.loads(self.s.recv(max_chunk))=='ok'):
            self.s.close()
            sys.exit(0)


#Entering the ip address and portno of the server
ip_address=input("\n\nEnter the ip address of the server\n")
port_no=int(input("Enter the portno of the server\n"))

p=peer(ip_address,port_no,5)


while True:
    #methods which can be done
    #select any one of the below
    print("\n\n1.Register and Seed\n")
    print("2.Search and Download\n")
    print("3.Quit\n")

    choice=int(input("Enter your choice(1/2/3):\n"))
    if(choice==1):
        #for registering the file
        file_name=input("\n\nEnter the filename to register:\n")
        try:
            #try opening the file
            file=open(file_name,'r')
        except(FileNotFoundError):
            print("File not found in this directory\n")
        else:
            file.close()
        a=p.register(file_name)
        #result of registering the file to the centralized directory
        if(a=='okay'):
            print("\nRegistration and seeding successful")
        else:
            if(a):
                print("\nRegistration successful but seeding failed")
            else:
                print("\nRegistration and seeding failed")
    elif(choice==2):
        file_name=input("Enter the filename to search:\n")
        b=p.search(file_name)
        if(b=='sch'):
            print("Only search successful")
        else:
            if(b):
                print("search and download successful")
            else:
                print("search and download failed")
    elif(choice==3):
        p.quit()






