#!/bin/bash

# Camaras Cabeza: 
# ip: 192.168.123.13
# user: unitree
# password: 123
############################################################################
# Camaras Lados: 
# ip: 192.168.123.14
# user: unitree
# password: 123
############################################################################
# Camara abajo/Cuerpo: 
# ip: 192.168.123.15
# user: unitree
# password: 123
############################################################################
# Raspberry PI:
# ip: 192.168.12.1
# user: pi
# password: 123

# Parametros Conexion SSH
SSH_USER="unitree"
SSH_HOST="192.168.123.15"
SSH_PASS="123"

# Estructura configuracion ROS
# # En la terminal del robot
# export ROS_MASTER_URI=http://IP_CEREBRO:11311
# export ROS_HOSTNAME=IP_ZONA_ROBOT
############################################################################
# En la terminal del ordenador
# export ROS_MASTER_URI=http://IP_RASPBERRY_PI:11311
# export ROS_HOSTNAME=IP_ORDENADOR

# Parametros ROS ROBOT
ROS_MASTER_URI_ROBOT="192.168.123.161"
ROS_HOSTNAME_ROBOT="192.168.123.15"
# Parametros ROS PC
ROS_MASTER_URI_PC="192.168.12.1"
ROS_HOSTNAME_PC="IP_PC"

# Funcion: Conexion SSH y configuracion ROS en ROBOT
conexion_ssh(){
    gnome-terminal -- bash -c "sshpass -p '$SSH_PASS' ssh $SSH_USER@$SSH_HOST;
                               export ROS_MASTER_URI=http://$ROS_MASTER_URI_ROBOT:11311;
                               export ROS_HOSTNAME=$ROS_HOSTNAME_ROBOT;
                               exec bash"
}

# Funcion: Configuracion ROS en PC
configuracion_ros(){
    export ROS_MASTER_URI="http://$ROS_MASTER_URI_PC:11311"
    export ROS_HOSTNAME="$ROS_HOSTNAME_PC"
}

configuracion_ros
conexion_ssh