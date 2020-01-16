#!/usr/bin/env python3
'''
Class: CPSC 471 - Computer Communications
Team: Dion W. Pieterse, Justin Chin, Ruchi Bagwe, Randy Baldwin
Project: FTP Server & FTP Client
Semester: Spring 2019
'''
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import argparse
import os
import subprocess
import sys
import time

LOW_PORT_LIMIT = 1024
HIGH_PORT_LIMIT = 65535


def log(func, cmd):
    logmsg = time.strftime("%Y-%m-%d %H-%M-%S [-] " + func)
    print("\033[31m%s\033[0m: \033[32m%s\033[0m" % (logmsg, cmd))


def port_type(port_str):
    """
    Command line argument type for legal port
    """
    port = int(port_str)
    if port < LOW_PORT_LIMIT or port > HIGH_PORT_LIMIT:
        raise argparse.ArgumentTypeError("Port number must be in the range [1024, 65535]")
    return port


def validate_args():
    """
    Returns port used for control connection.
    Creates argument parser to enforce proper command line argument
    usage.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('server_port',
                        nargs="?",
                        help='server port',
                        type=port_type,
                        default="3321")
    args = parser.parse_args()
    serverControlPort = args.server_port
    log('validate_args', 'server port = {}'.format(serverControlPort))
    return serverControlPort


def setup_ctrl_channel(port):
    """
    Returns a tuple for control connection btwn server & client.
    Instantiates a new TCP socket using IPv4, binding it to localhost.
    This socket is used as the control connection between the client
    and server FTP processes. All control commands (e.g ls, get, put,
    quit) are communicated on this channel.
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.bind(('', port))
        s.listen(1)
        log('setup_ctrl_channel', 'nextgenFTP server is ready')
        return s.accept()


def build_header(data):
    """
    Returns a new header 10 bytes in length.
    Computes the length (bytes) of passed arg, padding the
    result with '*'s appended to the right of the header.
    E.g data is 2222 bytes long, then header will be '2222******'
    """
    HEADER_BYTE_SIZE = 10
    try:
        header = str(len(bytes(data.encode('utf-8'))))  # size in bytes
    except:
        header = str(len(data))
    while len(header) < HEADER_BYTE_SIZE:
        header += '*'
    return header


def send_message(sock, payload):
    """
    Transfers payload to connected client process via sock
    """
    bytes_sent = 0
    header = build_header(payload)
    # concatenate header with payload to get entire message
    # being sent to client as string.
    try:
        message = ''
        message = header + payload

        while bytes_sent != len(bytes(message.encode('utf-8', errors='ignore'))):
            chunk = message[bytes_sent:]
            chunk = chunk.encode('utf-8', errors='ignore')
            bytes_sent += sock.send(chunk)
        log('send_message', 'sent {} bytes to client'.format(bytes_sent))
    except:
        message = bytes()
        message = bytes(header.encode('utf-8')) + payload

        while bytes_sent != len(message):
            chunk = message[bytes_sent:]
            bytes_sent += sock.send(chunk)
        log('send_message', 'sent {} bytes to client'.format(bytes_sent))


def receive_message(socket_name):
    HEADER_BYTE_SIZE = 10
    header = ''
    data_buffer = ''
    data_body = bytes()
    # receive first 10 bytes of message, parse as header
    while len(header) < HEADER_BYTE_SIZE:
        # use seperate variable, data_buffer, here instead of
        # appending to header directly because we want to check if we
        # received nothing from the socket, which informs the process
        # that the client has closed the connection
        data_buffer = socket_name.recv(HEADER_BYTE_SIZE)

        # client closes socket
        if not data_buffer:
            break
        # (turn bytes to string again)
        data_buffer = data_buffer.decode()
        header += data_buffer
    message_length = int(header.rstrip('*'))
    # extract body of message
    # reset the buffer to 0
    data_buffer = bytes()
    while len(data_body) < message_length:
        data_buffer = socket_name.recv(message_length)
        # client closes socket
        if not data_buffer:
            break
        data_body += data_buffer
        log('receive_message', 'received {} bytes'.format(len(data_buffer)))
    log('receive_message', 'transfer complete: {} bytes received'.format(len(data_body)))
    return data_body


def new_data_socket():
    send_message(ctrl_conn_sock, str(data_port))
    p = receive_message(ctrl_conn_sock)
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('', data_port))
    s.connect((client_addrss[0], int(p)))
    log('new_data_socket', s)
    return s


def verify_client_cmd(client_cmd):
    """
    Trampolines the process to the correct command
    """
    client_cmd = client_cmd.decode('utf-8')
    cmd_list = client_cmd.split()
    # DS to store valid tokens equating to FTP methods
    cmd_dictionary = {
        'get': get_cmd,
        'getb': getb_cmd,
        'put': put_cmd,
        'putb': putb_cmd,
        'ls': ls_cmd,
        'help': help_cmd,
        'quit': quit_cmd
    }
    # verify if token is in cmd list, call method from DS directly via reference
    if cmd_list[0] in cmd_dictionary:
        cmd_dictionary[cmd_list[0]](client_cmd)
    else:
        log('verify_client_cmd', 'Invalid command received: {}'.format(client_cmd))


def get_cmd(client_cmd):
    # establish data connection
    log('get_cmd', 'executing {}'.format(client_cmd))
    cmd = client_cmd.split()  # cmd[0]: get, cmd[1]: filename
    file_path = os.path.join(os.getcwd(), cmd[1])

    with new_data_socket() as s:
        # check if file exists
        if os.path.isfile(file_path):
            send_message(s, 'File exists!')
            with open(file_path, mode='r', newline='') as fo:
                log('get_cmd', 'opening file {}'.format(file_path))
                file_data = fo.read()

                # send message to client
                send_message(s, file_data)
        else:
            send_message(s, '')
            log('get_cmd', 'file {} does not exist'.format(file_path))


def getb_cmd(client_cmd):
    # establish data connection
    log('getb_cmd', 'executing {}'.format(client_cmd))

    cmd = client_cmd.split()  # cmd[0]: get, cmd[1]: filename
    file_path = os.path.join(os.getcwd(), cmd[1])

    with new_data_socket() as s:
        # check if file exists
        if os.path.isfile(file_path):
            send_message(s, 'File exists!')
            with open(file_path, mode='rb') as fo:
                log('get_cmd', 'opening file {}'.format(file_path))
                file_data = fo.read()

                # send message to client
                send_message(s, file_data)
        else:
            send_message(s, '')
            log('get_cmd', 'file {} does not exist'.format(file_path))


def put_cmd(client_cmd):
    log('put_cmd', 'executing {}'.format(client_cmd))

    cmd_list = client_cmd.split()
    basename = os.path.basename(cmd_list[1])
    filepath = os.path.join(os.getcwd(), basename)

    with new_data_socket() as s:
        with open(filepath, mode='w', encoding='utf-8', newline='') as fo:
            data = receive_message(s)
            fo.write(data.decode('utf-8'))


def putb_cmd(client_cmd):
    log('putb_cmd', 'executing {}'.format(client_cmd))

    cmd_list = client_cmd.split()
    basename = os.path.basename(cmd_list[1])
    filepath = os.path.join(os.getcwd(), basename)

    with new_data_socket() as s:
        with open(filepath, mode='wb') as fo:
            data = receive_message(s)
            fo.write(data)


def ls_cmd(client_cmd):
    log('ls_cmd', 'execeuting {}'.format(client_cmd))
    with new_data_socket() as s:
        send_message(s, subprocess.getoutput(client_cmd))


def help_cmd(client_cmd):
    log('help_cmd', 'executing {}'.format(client_cmd))
    all_data = ''

    with new_data_socket() as s:
        msg = ['************************\n',
               '*** List of Commands ***\n',
               '************************\n',
               '*       help           *\n',
               '*        ls            *\n',
               '*    get <filename>    *\n',
               '*   getb <filename>    *\n',
               '*   putb <filename>    *\n',
               '*   put <filename>     *\n',
               '*       quit           *\n',
               '************************\n']

        for row in msg:
            all_data += row
        send_message(s, all_data)


def quit_cmd(client_cmd):
    # Notify the user that the connection is closed
    log('quit_cmd', 'closing connection with {}'.format(client_addrss))

    # close the control channel out before exiting
    ctrl_conn_sock.close()

    # close the program
    sys.exit(0)


"""
##############################################################
################# MAIN #######################################
##############################################################
"""
ctrl_port = validate_args()
data_port = ctrl_port - 1

ctrl_conn_sock, client_addrss = setup_ctrl_channel(ctrl_port)

with ctrl_conn_sock:
    log('main', '{} connected on port {}'.format(client_addrss[0], client_addrss[1]))
    send_message(ctrl_conn_sock, 'Welcome to nextgenFTP')

    # Keep accepting incoming connections from client
    while True:
        client_cmd = receive_message(ctrl_conn_sock)
        verify_client_cmd(client_cmd)
