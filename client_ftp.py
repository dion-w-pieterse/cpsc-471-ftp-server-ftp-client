#!/usr/bin/env python3

'''
Class: CPSC 471 - Computer Communications
Team: Dion W. Pieterse, Justin Chin, Ruchi Bagwe, Randy Baldwin
Project: FTP Server & FTP Client
Semester: Spring 2019
'''
from socket import socket, AF_INET, SOCK_STREAM
import argparse
import sys
import os
import time

TOGGLE_TXT_FMTING = 0
VALID_CMD = 0
INVALID_IP_MSG = 'Invalid IP address or domain name.'
VALID_IP_MSG = 'The server IP is valid.'
INVALID_FTP_MSG = 'Invalid FTP command. Type: \'help\' for list of valid commands.'
LOW_PORT_LIMIT = 1024
HIGH_PORT_LIMIT = 65535


def log(func, cmd):
    logmsg = time.strftime("%Y-%m-%d %H-%M-%S [-] " + func)
    print("\033[31m%s\033[0m: \033[32m%s\033[0m" % (logmsg, cmd))


def prog_header():
    graphic = ['                                                         ',
               '                    __                   ________________ ',
               '   ____  ___  _  __/ /_____ ____  ____  / ____/_  __/ __ \\',
               '  / __ \\/ _ \\| |/_/ __/ __ `/ _ \\/ __ \\/ /_    / / / /_/ /',
               ' / / / /  __/>  </ /_/ /_/ /  __/ / / / __/   / / / ____/ ',
               '/_/ /_/\\___/_/|_|\\__/\\__, /\\___/_/ /_/_/     /_/ /_/      ',
               '                    /____/                                 ',
               '                                                            ']

    for line in graphic:
        # print('%s%s%s%s' % (fg('yellow'), attr('bold'), line, attr('reset')))
        print_fmt_txt('yellow', 'bold', line)


def port_type(port_str):
    port = int(port_str)
    if port < LOW_PORT_LIMIT or port > HIGH_PORT_LIMIT:
        raise argparse.ArgumentTypeError("Port number must be in the range [1024, 65535]")
    return port


def validate_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('server_machine', help='the address of the server')
    parser.add_argument('server_port',
                        nargs="?",
                        help='the connection port',
                        type=port_type,
                        default="3321")

    args = parser.parse_args()
    serverName = args.server_machine
    serverControlPort = args.server_port
    return (serverName, serverControlPort)


def concat_list_elems(list_ds):
    final_str = ''
    for elem in list_ds:
        final_str += str(elem)
    result = int(final_str)
    return result


def build_header(data_amt):
    HEADER_BYTE_SIZE = 10
    header_section = str(len(data_amt))

    while len(header_section) < HEADER_BYTE_SIZE:
        header_section += '*'
    return header_section


def send_message(socket_name, data_body):
    bytes_sent = 0
    header = build_header(data_body)

    # quick solution for raw byte transfers
    try:
        entire_msg = ''
        entire_msg = header + data_body

        # send all the information to server
        while bytes_sent != len(bytes(entire_msg.encode('utf-8'))):
            data_chunk = entire_msg[bytes_sent:]
            data_chunk = data_chunk.encode()
            bytes_sent += socket_name.send(data_chunk)
        log('send_message', 'sent {} bytes to server'.format(bytes_sent))

    except:
        entire_msg = bytes()
        entire_msg = bytes(header.encode('utf-8')) + data_body

        while bytes_sent != len(entire_msg):
            chunk = entire_msg[bytes_sent:]
            bytes_sent += socket_name.send(chunk)


def receive_message(socket_name):
    HEADER_BYTE_SIZE = 10
    header = ''
    data_buffer = ''
    data_body_size = 0
    data_body = bytes()

    while len(header) < HEADER_BYTE_SIZE:
        data_buffer = socket_name.recv(HEADER_BYTE_SIZE)
        # server closes socket
        if not data_buffer:
            break
        # (turn bytes to string again)
        data_buffer = data_buffer.decode()
        header += data_buffer

    # form the actual data_body size
    data_body_size = int(header.rstrip('*'))

    # extract body of message
    # reset the buffer to 0
    data_buffer = ''
    while len(data_body) < data_body_size:
        data_buffer = socket_name.recv(data_body_size)
        # server closes socket
        if not data_buffer:
            break

        data_body += data_buffer
        log('receive_message', 'received {} bytes'.format(len(data_buffer) + len(header)))
    # end extract data_body
    log('receive_message', 'transfer complete: {} bytes received.'.format(len(data_body)))
    return data_body


def print_fmt_txt(foregrnd, style, txt):
    if TOGGLE_TXT_FMTING == 1:
        print('%s%s%s%s' % (fg(foregrnd), attr(style), txt, attr('reset')))
    else:
        print(txt)


def setup_data_trfr_socket(server_address, control_sock):
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    send_message(control_sock, str(s.getsockname()[1]))
    return s.accept()


def process_ls_cmd(socket_name):
    data_body = receive_message(socket_name)
    print_fmt_txt('yellow', 'bold', data_body.decode('utf-8'))


def process_get_cmd(socket_name, path):
    filename = os.path.basename(path)
    exists = receive_message(socket_name)

    if exists:
        with open(filename, mode='w', encoding='utf-8', newline='') as f:
            data = receive_message(socket_name)
            f.write(data.decode('utf-8'))
    else:
        print('File does not exist.')


def process_put_cmd(socket_name, path):
    path = os.path.join(os.getcwd(), path)
    if os.path.isfile(path):
        # send the file over to the server
        with open(path, mode='r', encoding='utf-8', newline='') as f:
            file_data = f.read()
            send_message(socket_name, file_data)
    else:
        print('File does not exist.')


def process_help_cmd(socket_name):
    data_body = receive_message(socket_name)
    print_fmt_txt('yellow', 'bold', data_body.decode('utf-8'))


def process_getb_cmd(socket_name, path):
    filename = os.path.basename(path)
    exists = receive_message(socket_name)
    if exists:
        with open(filename, mode='wb') as f:
            data = receive_message(socket_name)
            f.write(data)
    else:
        print('File does not exist.')


def process_putb_cmd(socket_name, path):
    path = os.path.join(os.getcwd(), path)

    if os.path.isfile(path):
        # send the file over to the server
        with open(path, mode='rb') as f:
            file_data = f.read()
            send_message(socket_name, file_data)
    else:
        print('File does not exist.')


"""
##############################################################
################# MAIN ENTRY #################################
##############################################################
"""
# set server info and server address tuple after validation
serverName, serverAddress = validate_args()
serverAddress = (serverName, serverAddress)

prog_header()
with socket(AF_INET, SOCK_STREAM) as clientSocket:
    # establish command channel with server (pass commands through this channel ONLY)
    clientSocket.connect(serverAddress)

    # notfy command channel established with respective server
    print('Connected to ', serverAddress)

    # Print the received welcome string
    print(receive_message(clientSocket).decode('utf-8'))

    while True:
        # Request input from user
        command = input('ftp> ')

        # *** Note *** #
        # Complex commands like 'ls -al' are identified by the first token 'ls'
        # It is not just string matching. I validate_cmd and check first element
        cmd_list = command.split()

        if command == 'quit':
            # one way message, not expecting anything back
            send_message(clientSocket, command)
            print('Connection with', serverAddress, 'closed')
            sys.exit(0)

        elif cmd_list[0] == 'ls':
            send_message(clientSocket, command)
            datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
            process_ls_cmd(datasock)
            datasock.close()

        elif cmd_list[0] == 'get':
            if len(cmd_list) > 1:
                send_message(clientSocket, command)
                datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
                process_get_cmd(datasock, cmd_list[1])
                datasock.close()
            else:
                print('Usage: get <file>')

        elif cmd_list[0] == 'put':
            if len(cmd_list) > 1:
                send_message(clientSocket, command)
                datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
                process_put_cmd(datasock, cmd_list[1])
                datasock.close()
            else:
                print('Usage: put <file>')

        elif cmd_list[0] == 'getb':
            if len(cmd_list) > 1:
                send_message(clientSocket, command)
                datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
                process_getb_cmd(datasock, cmd_list[1])
                datasock.close()
            else:
                print('Usage: getb <file>')

        elif cmd_list[0] == 'putb':
            if len(cmd_list) > 1:
                send_message(clientSocket, command)
                datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
                process_putb_cmd(datasock, cmd_list[1])
                datasock.close()
            else:
                print('Usage: putb <file>')

        elif cmd_list[0] == 'help':
            send_message(clientSocket, command)
            datasock, _ = setup_data_trfr_socket(serverName, clientSocket)
            process_help_cmd(datasock)
            datasock.close()

        else:
            print_fmt_txt('yellow', 'bold', INVALID_FTP_MSG)
