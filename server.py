import socket
import uuid
#generating 4-bytes random ids
import pickle
#for serializing and deserializing python object structure
import threading
#creating multiple threads
import sys

port=9300
max_chunk=1024

class server:
    def __init__(self,port,no_of_connections):
        self.port=port #portno of this machine
        self.host=socket.gethostbyname(socket.gethostname()) #ip of this machine
        self.no_of_connections=no_of_connections#no.of connections
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.file={}#list of files registered
        self.peers={}#list of peers connected

        x=True
        while x:
            try:
                self.sock.bind((self.host,self.port))
            except OverflowError:
                self.port=input("Enter new port(>3000)")#alternative portno
            else:
                x=False

        print("listening through [",self.host,":",self.port,"]")




    def peer_threads(self,client,addr):

        peer_id=uuid.uuid4().int>>115
        #generates unique id for each peer

        self.peers[peer_id]=addr
        #appending peer spacifications to list of peers

        client.send(pickle.dumps((peer_id,addr[1])))
        #sending peerid to the recipient and also the portno for connection


        while True: 
            method=pickle.loads(client.recv(max_chunk))     

            print("Method opted by peer_id-",peer_id," is ",method)

            if(method=="search"):
                #searching a file in the centralized directory
                client.send(pickle.dumps("ok"))
                file_name=pickle.loads(client.recv(max_chunk))
                #loading up the name of the file needed for searching

                if(file_name in self.file):
                    client.send(pickle.dumps('found'))
                    reply=pickle.loads(client.recv(max_chunk))
                    #getting reply from the peer whether to send or not

                    if(reply=='send'):#peer asks to send
                        content=pickle.dumps(self.file[file_name])
                        client.send(content)

                       #In case of files contained by many peers
                        #selection of file from which peer is needed
                        peerno=pickle.loads(client.recv(max_chunk))
                        client.send(pickle.dumps(self.peers[peerno]))
                    else:
                        "only search is done.."
                else:
                    #file not found(invalid one)
                    client.send(pickle.dumps("not found"))
        

            elif(method=='register'):
                #registering files to the server by peers
                #in order to access
                client.send(pickle.dumps('ok'))
                file_name=pickle.loads(client.recv(max_chunk))
                print("For registering file by peer_id-",peer_id)

                if file_name in self.file:
                    self.file[file_name].append(peer_id)
                #in case of file contained only the peerids are noted for 
                #the file
                else:
                    self.file[file_name]=[]
                    self.file[file_name].append(peer_id)
                #new file list created and peerids are appended
                client.send(pickle.dumps('success'))

            elif(method=='bye'):
                client.send(pickle.dumps('ok'))

                list1=[]

            #peerids present in the files are deleted in file list
            #if file[file_name] is empty
            #then file_name should be deleted in register

                for i in self.file:
                    try:
                        self.file[i].remove(peer_id)
                        if(self.file[i]==[]):
                            list1.append(i)
                    except ValueError:
                        continue
                    

                #peerids are deleted in peers list
                del self.peers[peer_id]
                sys.exit(0)



    def connections(self):
        thread_id=[]
        self.sock.listen(self.no_of_connections)
        
        while True:
            client,addr=self.sock.accept()   #accepting connections
            print("Connected with ",addr)


            #thread creation for each peer
            try:
                t=threading.Thread(target=self.peer_threads,args=(client,addr))
                #creating threads and passing arguments
                t.start()
                #starting the thread
                print("thread started")


            except:
                print("Thread didn't start")

        self.sock.close()


if __name__=='__main__':
    s=server(port,5)
    s.connections()