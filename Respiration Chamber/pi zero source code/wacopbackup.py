# -*- coding: utf8 -*-
# 작동순서
# 1) GUI 프로그램 통신, 전원 연결 후 약 20초 내에 연결 해야함, 20초 후 Main문으로 넘어감
# 1-1) GUI 통신을 통해 config 파일을 받고 저장
# 1-2) Cycle카운트, 대기시간 후 bottle에 물 채우는 량(ml), Cycle마다 물 교체량(ml), 중간 대기시간
# 2) 첫 번째 Cycle 시작 전에 bottle에 물 채우는 량만큼 필 펌프 동작, 튜브에 물을 채우기위해 스터러거도 잠시 동작(약 2~3분)
# 2-1) (2) 전까지는 대기모드(sleep)
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# 3) Cycle 시작시간에 맞게 산소센서, 조도센서 작동시작
# 3-1) 센서 데이터 저장(로깅)
# 3-2) Cycle Measure_time_Day Measure_time_Hour Oxyzen_value_1 Oxyzen_value_2 Temp_value_1 Temp_value_2 THL_FLX THL_Temp Stir_pump_working Pill_pump_working
# 3-3) Cycle번호, 측정날짜, 시간, 산소데이터_1, 산소데이터_2, 온도데이터_1, 온도데이터_2, 조도센서_광량데이터, 조도센서_온도데이터, 스터러거_작동여부, 필펌프_작동여부
# 3-4) 스터러거_작동여부, 필펌프_작동여부는 0과1로, 0이면 작동하지 않는 상태 1이면 작동하고 있는 상태
# 4) 중간 대기시간이 되면 스터러거 멈춤, 센서데이터는 계속 저장됨
# 4-1) 다음 Cycle 넘어가기 전에 물 교체
# 4-2) (3)~(4)를 반복
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# 5) 마지막 Cycle이 끝나더라도 계속 센서데이터는 로깅됨

from datetime import datetime
import serial
import time
import RPi.GPIO as GPIO
import os
import math

StirA_1 = 1
StirA_2 = 7
StirB_1 = 8
StirB_2 = 25

FillA_1 = 26
FillA_2 = 19
FillB_1 = 6
FillB_2 = 5

Buzzerpin = 0

stir_pwm_pin=12
fill_pwm_pin=13

# 시리얼 포트 익스펜더 핀 정의
# 이진수 방식으로 채널 변경
# Ex) s1 = 0, s2 = 0, s3 = 0 면 1채널

GPIO.setmode(GPIO.BCM)
GPIO.setup(16,GPIO.OUT) #s1
GPIO.setup(20,GPIO.OUT) #s2
GPIO.setup(21,GPIO.OUT) #s3

GPIO.setup(stir_pwm_pin,GPIO.OUT)
GPIO.setup(fill_pwm_pin,GPIO.OUT)

GPIO.setup(StirA_1,GPIO.OUT)
GPIO.setup(StirA_2,GPIO.OUT)
GPIO.setup(StirB_1,GPIO.OUT)
GPIO.setup(StirB_2,GPIO.OUT)

GPIO.setup(FillA_1,GPIO.OUT)
GPIO.setup(FillA_2,GPIO.OUT)
GPIO.setup(FillB_1,GPIO.OUT)
GPIO.setup(FillB_2,GPIO.OUT)

GPIO.setup(Buzzerpin,GPIO.OUT)



GPIO.output(StirA_1,GPIO.HIGH)
GPIO.output(StirA_2,GPIO.LOW)

GPIO.output(StirB_1,GPIO.LOW)
GPIO.output(StirB_2,GPIO.HIGH)

GPIO.output(FillA_1,GPIO.HIGH)
GPIO.output(FillA_2,GPIO.LOW)

GPIO.output(FillB_1,GPIO.LOW)
GPIO.output(FillB_2,GPIO.HIGH)

GPIO.output(Buzzerpin,GPIO.HIGH)

#PWM(pin,Hz)
stir_pwm=GPIO.PWM(stir_pwm_pin,1000)
fill_pwm=GPIO.PWM(fill_pwm_pin,1000)


pi_pwm1.start(0)
pi_pwm2.start(0)

stir_pwm.ChangeDutyCycle(0) #set pwm1 percent
fill_pwm.ChangeDutyCycle(0) #set pwm2 percent

# 산소센서 시리얼 주소 정의
# Port, Baudrate는 고정

ser = serial.Serial(
        port='/dev/ttyS0', #Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
        baudrate = 19200,
        parity=serial.PARITY_NONE,       
        stopbits=serial.STOPBITS_ONE, 
        bytesize=serial.EIGHTBITS,        
        timeout=1
)
ser.flush()





# 소스코드에 필요한 리스트, 변수 정의
os_list = []
os_list_2 = []
#us_list = []
ps_list_O = []
ps_list_T = []
ps_list_T_2 = []
ps_list_O_2 = []
os_list_3 = []
gui_list = []
gui_list_2 = [0]
data_inform = []
fill = [0]
fill_2 = [0]
stir = [0]
stir_2 = [0]
z = []
chZ=[]

data = 0
data_index_O = 0
data_index_T = 0
result_O = 0
result_T = 0
next_starttime = 0
time_diff_2 = 0
gui_host = 0
gui_count = 1
startgun = 1
startflag = 1
top=1



# ★★★★★★★★★★★★★★★★★★★★★
# 시리얼 익스펜더 채널 바꾸는 함수
# 2진수를 기반으로 작동
# 산소센서 2개는 1,2 채널 - 조도센서 3채널
# 스터러거 2개는 4,5 채널 - 필모터는 6,7 채널
# ★★★★★★★★★★★★★★★★★★★★★

def convert_size(size_bytes): #파일 크기 변환함수
    if size_bytes == 0:
        return "0Byte"
    size_name = ("Byte", "KiB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s%s" % (s, size_name[i])

def change_channel(number): #시리얼 채널 바꾸는 함수
    number = number - 1
    income = number // 4
    if income == 1:
        GPIO.output(21,True)
        number = number - 4
    else:
        GPIO.output(21,False)
    income = number // 2
    if income == 1:
        GPIO.output(20,True)
        number = number - 4
    else:
        GPIO.output(20,False)
    income = number % 2
    if income == 1:
        GPIO.output(16,True)
        number = number - 4
    else:
        GPIO.output(16,False)
        
    time.sleep(0.5)
    print("change complete")

# ★★★★★★★★★★★★★★
# 산소센서 작동 시작 함수 
# mode0000 산소센서 작동 시작
# mode0001 산소센서 작동 중지
# repo 산소센서 설정확인
# ★★★★★★★★★★★★★★
    
def start_mode(): #산소센서 켜는 함수
    change_channel(1)
    ut = "mode0000"
    ser.write("\r".encode('utf-8'))
    ser.write((ut+"  "+"\r").encode('utf-8'))

    time.sleep(0.5)
    change_channel(2)
    ser.write("\r".encode('utf-8'))
    ser.write((ut+"  "+"\r").encode('utf-8'))
    time.sleep(0.5)

# 모터 작동 시작 함수, 시리얼 통신(UART)
# 'D, *' => 105 ml/min (최대치)
# 'D, 50' => 105 ml/min 로 물 50 ml 채움
# 'DC, 30, 100' => 30 ml/min 로 100분 동안 작동 
    
def stir_motor_start(): 
    stir[0] = 1
    stir_pwm.ChangeDutyCycle(20) #set pwm percent
    
    """
    change_channel(4)
    ut = "DC,40,1000"+"\r"
    ser.write(ut.encode('utf-8'))
    time.sleep(0.5)
    change_channel(5)
    ser.write(ut.encode('utf-8'))
    time.sleep(0.5)
    """

# 모터 멈춤 함수
# 'X' => 모터 멈춤
    
def stir_motor_stop():
    stir[0] = 0
    stir_pwm.ChangeDutyCycle(0) #set pwm percent
    
    """
    change_channel(4)
    ut = "X"
    ser.write((ut+"\r").encode('utf-8'))
    time.sleep(1)
    change_channel(5)
    ser.write((ut+"\r").encode('utf-8'))
    time.sleep(1)
    """
    
def motor_check():
    if fill[0] == 1 and stir[0] == 0 :
        stir_2[0] = 0
        fill_2[0] = 1
        
    if fill[0] == 0 and stir[0] == 1 :
        stir_2[0] = 1
        fill_2[0] = 0
        
    if fill[0] == 0 and stir[0] == 0 :
        fill_2[0] = 0
        stir_2[0] = 0
    
    if fill[0] == 1 and stir[0] == 1 :
        fill_2[0] = 0
        stir_2[0] = 0
        
# 다음 Cycle전에 bottle에 물을 바꾸기 위한 함수

def fill_motor_start(number, time_diff):
    try:
        global Fill_pump_working
        delay_time_sec = int(fileMatrix[number+2][3])*60
        fill_motor_sec = float(float(int(fileMatrix[number+2][4])/90) * 60)
        fill_motor_sec_2 = float(float(int(fileMatrix[number+2][4])/105) * 60)
        pump_ml = int(fileMatrix[number+2][4])
        if time_diff >= delay_time_sec - 10 and time_diff <= delay_time_sec + 10 :
            stir_motor_stop()
        
        elif time_diff >=  fill_motor_sec - 10 and time_diff <=  fill_motor_sec + 10 :
            fill[0] = 1
            fill_pwm.ChangeDutyCycle(50) #set pwm percent
    
    """
            pump_order = "D,"+str(pump_ml)+"\r"
            time.sleep(0.5)
            change_channel(6)
            ser.write("\r".encode('utf-8'))
            ser.write(pump_order.encode('utf-8'))
            time.sleep(0.5)
            change_channel(7)
            ser.write("\r".encode('utf-8'))
            ser.write(pump_order.encode('utf-8'))
            time.sleep(0.5)
            """
            stir_motor_start()
            
        elif time_diff <= fill_motor_sec - fill_motor_sec_2:
            fill[0] = 0
            fill_pwm.ChangeDutyCycle(0) #set pwm percent
    
    except:
        pass
        
# 다음 Cycle전에 bottle에 물을 바꾸기 위한 함수

def delay_time_sleep():
    try:
        #nowf = datetime.now()
        #now_comparef = now.strftime("%Y-%m-%d %H:%M:%S")
        #start_timef = datetime.strptime(str(fileMatrix[2][1])+" "+str(fileMatrix[2][2]),"%Y-%m-%d %H:%M:%S")
    
        #시작시간까지의 차이
        #delaytimef = (start_timef-nowf).seconds
        first_stir_flag = False
        print(delaytime)
        
        delay_pump_ml = int(fileMatrix[0][3]) #펌프할 ml
        print(delay_pump_ml)
        delay_time_sec = (delay_pump_ml / 90)*60 #물을 가는데 걸리는 시간
        sleep_time = abs(int(delaytime - delay_time_sec-30)) #프로그램 시작후 펌프가 물을 바꾸기 위해 켜는데 까지 시간
        print("sleep_time : "+str(sleep_time))
        time.sleep(sleep_time) #sleeptime 이후에 fill모터들 작동
        
        
        fill_pwm.ChangeDutyCycle(45)
        """
        change_channel(6) #fill모터 1번 켜기
        pump_order = "D,"+str(delay_pump_ml)+"\r"
        ser.write("\r".encode('utf-8'))
        ser.write(pump_order.encode('utf-8'))
        time.sleep(1)
        
        change_channel(7) #fill모터 2번 켜기
        ser.write("\r".encode('utf-8'))
        ser.write(pump_order.encode('utf-8'))
        time.sleep(1)
        """
        
        while(1):
            now = datetime.now()
            now_compare = now.strftime("%Y-%m-%d %H:%M:%S") #지금 시간
            now_int = now.strftime("%Y%m%d%H%M%S")   
            start_compare = datetime.strptime(str(fileMatrix[2][1])+" "+str(fileMatrix[2][2]),"%Y-%m-%d %H:%M:%S") #정해진 첫 번째 시작시간
            time_diff = int((start_compare - now).seconds) #두시간만큼의 차이
            print("until start time: "+str(time_diff))
            time.sleep(0.5)
            if(time_diff <= 20):
                fill_pwm.ChangeDutyCycle(0)          
            if(time_diff <= 2): #프로그램 시작시간이 다되면
                break;
            if(time_diff <= 180 and first_stir_flag == False): #프로그램 설정 시작시간보다 3분전이면 스트로거 작동시킴
                first_stir_flag = True
                
                stir_motor_start()
                """
                change_channel(4)
                pump_order = "D,200"+"\r"
                ser.write("\r".encode('utf-8'))
                ser.write(pump_order.encode('utf-8'))
                time.sleep(0.5)
                change_channel(5)
                pump_order = "D,200"+"\r"
                ser.write("\r".encode('utf-8'))
                ser.write(pump_order.encode('utf-8'))
                time.sleep(0.5)
                """
                
    except:
        pass
            

stir_motor_stop()
start_mode()




#time.sleep(5)#3초 대기 후 검사

change_channel(1)
checkp=ser.readline().decode('utf-8') #산소센서1번 값 보내는지 확인
print('check OX1')
change_channel(2)
checkp=ser.readline().decode('utf-8') #산소센서2번 값 보내는지 확인
print('check OX2')
change_channel(3)
#checkp=ser.readline().decode('utf-8')
#chZ.append(ser.readlines()[-1].decode('ascii')) #조도센서 값 보내는지 확인
"""

"""
change_channel(1)
top_2 = 1
while(top_2):
    try:
        x=ser.readline().decode('utf-8')
        os_list.append(x)
        time.sleep(0.5)
        
        for k in os_list:
            if "N" in k:
                data=k
                data_index_T = int(data.index('T'))
                data_index_O = int(data.index('O'))
                ps_list_T.append(data[data_index_T+1:data_index_T+5])
                ps_list_O.append(data[data_index_O+1:data_index_O+7])
                
                print("TestT1 : ",ps_list_T[0])
                print("TestO1 : ",ps_list_O[0])
                
                top_2=0
                change_channel(2)
                best=1
    except:
        pass

while(best):
    best_2 = 1
    while(best_2):
        try:
            y=ser.readline().decode('utf-8')
            os_list_2.append(y)
            time.sleep(0.5)
            for y in os_list_2:
                if "N" in y:
                    data = y
                    data_index_T_2 = int(data.index('T'))
                    data_index_O_2 = int(data.index('O'))
                    ps_list_T_2.append(data[data_index_T_2+1:data_index_T_2+5])
                    ps_list_O_2.append(data[data_index_O_2+1:data_index_O_2+7])
                    
                    print("-----------------------------------------")
                    print("TestT2 : ",ps_list_T_2[0])
                    print("TestO2 : ",ps_list_O_2[0])
                    cron = 1
                    best = 0
                    best_2 = 0
                    change_channel(3) #조도센서3채널
        except:
            pass
        

    while(cron):
        ser.baudrate = 9600
        try :
            z.append(ser.readlines()[-1].decode('ascii'))
            z_2 = str(z[0])
            z.clear()
            os_list_3.append(z_2)
            time.sleep(0.5)
            for z_3 in os_list_3 :
                if "@T" in z_3:
                    data = z_2
                    data_inform = data.split(',')
                    data_inform_2 = float(data_inform[2])
                    data_inform_1 = float(data_inform[4].strip())
                                    
                    print("----------------------------------------")
                    print("TestFlx : " + str(data_inform_1))
                    print("TestTemp : " + str(data_inform_2))
                    print("----------------------------------------")
                    time.sleep(0.5)
                    ser.baudrate = 19200
                    time.sleep(0.5)
                    cron = 0
                    top = 0
                    
            best = 0
                
                
        except:        
            pass

os_list.clear()
ps_list_T.clear()
ps_list_O.clear()
                    
os_list_2.clear()
ps_list_T_2.clear()
ps_list_O_2.clear()
                        
os_list_3.clear()
data_inform.clear()
data=0
time.sleep(0.5)

ser.flush()
ser.close()
ser.open()

#센서들이 정상 작동을 하면 시그널로 스트러거모터동작시킴(GUI연결 여부확인 후 종료)
"""
change_channel(4)
ut = "DC,10,1000"+"\r" 
ser.write(ut.encode('utf-8'))
time.sleep(0.5)
change_channel(5)
ser.write(ut.encode('utf-8'))
time.sleep(0.5)
"""
cnt=0
ff=1
while(ff):
    GPIO.output(Buzzer,GPIO.HIGH)
    time.sleep(1)
    GPIO.output(Buzzer,GPIO.LOW)
    time.sleep(1)
    cnt=cnt+1
    if cnt == 10:
        ff=0


# GUI 연결 소스코드, 전원을 연결하고 약 20초내에 GUI와 연결해야함
# config 파일을 GUI프로그램에서 받고나서 무조건 전원을 다시 연결해야 Main문이 작동함
# 20초내에 GUI와 연결 안하면 Main문으로 넘어감

while(startgun):
    try:
        gui_count += 1
        print("gui_count : "+str(gui_count))
        if gui_count == 10:
            break
        elif gui_count ==4:
            stir_motor_stop()
        change_channel(8)
        time.sleep(1)
        
        g=ser.readline().decode('utf-8')
        gui_list.append(g)
        for x in gui_list :
            if "Start" in x :
                ser.write("CONNECT_SUCCESS".encode('utf-8'))
                print("connect success")
                time.sleep(1)
                stir_motor_stop()
                change_channel(8)
                #time.sleep(1)
                gui_host = 1
                try:
                    #stir_motor_stop()
                    #change_channel(8)
                    while(gui_host):
                        try:
                            g_4 = ser.readline().decode('utf-8')
                            gui_list_2[0] = g_4
                            for y in gui_list_2 :
                                if "Cycle" in y :
                                    print("config_detect")
                                    f_2 = open('./config.txt','w')
                                    mdata = y
                                    mdata = mdata.split()
                                    cycle_count = int(mdata[1])
                                    f_2.write(mdata[0]+" "+mdata[1]+" "+mdata[2]+" "+mdata[3]+" ")
                                    f_2.write("\n")
                                    for p in range(5):
                                        f_2.write(mdata[p+4]+" ")
                                    w = 0
                                    while(True):
                                        if w == int(mdata[1]):
                                            break
                                        for e in range(len(mdata)-9):
                                            if e % 4 == 0:
                                                f_2.write("\n")
                                                w += 1
                                                f_2.write(str(w)+" ")
                                            f_2.write(str(mdata[e+9])+" ")
                                    f_2.close()
                                    
                                if "TEXT_CONFIRM" in y :
                                
                                    k_number=1
                                    print(gui_list_2)
                                    time.sleep(0.5)
                                    while k_number:
                                        k_number=0
                                                                 
                                        ser.write("TEXT_TRANSFER\n".encode('utf-8'))
                                        file_list = os.listdir('/home/pi/logging_data')
                                        for i in range(len(file_list)):
                                            print(file_list[i])
                                            file_send=file_list[i]+"-"+convert_size(os.path.getsize('/home/pi/logging_data/'+file_list[i]))
                                            ser.write(file_send.encode('utf-8'))
                                            ser.write(" ".encode('utf-8'))
                                if "txt" in y:
                                    logging_file_name = y
                                    loggingfileMatrix = []
                                    file_path = '/home/pi/logging_data/'+logging_file_name

                                    with open(file_path) as file :

                                        for lineContent in file: # Point.1
                                            loggingfileMatrix.append(lineContent.strip('\n'))
                                    print("1")
                                    ser.write("LOGGINGDATA_TRANSFER\n".encode())
                                    for i in range(len(loggingfileMatrix)):
                                        ser.write(loggingfileMatrix[i].encode())
                                        ser.write("\n".encode())
                                    
                                
                                    ser.write("\n".encode())
                                    ser.write("END".encode())
                                if "Start" in y:
                                    ser.write("CONNECT_SUCCESS".encode('utf-8'))
                                if "StirOn" in y:
                                    stir_motor_start()
                                    #ser.write("StirOn_SUCCESS".encode('utf-8'))
                                    print("StirOn Success")
                                    #change_channel(8)
                                
                               
                                if "StirOff" in y:
                                    stir_motor_stop()
                                    print("StirOff Success")
                                    #change_channel(8)
                                
                                if "FillOn" in y:
                                    
                                    fill_pwm.ChangeDutyCycle(50)
                                    print("FillOn Success")
                                    """
                                    change_channel(6) #fill모터 1번 켜기
                                    pump_order = "D,1000\r"
                                    ser.write("\r".encode('utf-8'))
                                    ser.write(pump_order.encode('utf-8'))
                                    time.sleep(1)
        
                                    change_channel(7) #fill모터 2번 켜기
                                    ser.write("\r".encode('utf-8'))
                                    ser.write(pump_order.encode('utf-8'))
                                    time.sleep(1)
                                    print("FillOn Success")
                                    change_channel(8)
                                    """
                                if "FillOff" in y:
                                    
                                    fill_pwm.ChangeDutyCycle(0)
                                    print("FillOff Success")
                                    """
                                    change_channel(6) #fill모터 1번 켜기
                                    pump_order = "X\r"
                                    ser.write("\r".encode('utf-8'))
                                    ser.write(pump_order.encode('utf-8'))
                                    time.sleep(1)
        
                                    change_channel(7) #fill모터 2번 켜기
                                    ser.write("\r".encode('utf-8'))
                                    ser.write(pump_order.encode('utf-8'))
                                    time.sleep(1)
                                    print("FillOff Success")
                                    change_channel(8)
                                    """
                                
                                if "Delete" in y:
                                    
                                    cron=1
                                    while(cron):
                                        k_list = []
                                        k = ser.readline().decode('utf-8')
                                        k_list.append(k)
                                        for x in k_list:
                                            if "txt" in x:
                                                file_path="/home/pi/logging_data/"+x
                                                print(file_path)
                                                
                                                if os.path.exists(file_path):
                                                    os.remove(file_path)
                                                    cron=0

                                                #cron=0
                                            elif "no" in x:
                                                print("end")
                                                cron=0
                                                
                                            
                                
                                if "OxCheck" in y:
                                    change_channel(1)
                                    top_2 = 1
                                    while(top_2):
                                        try:
                                            x=ser.readline().decode('utf-8')
                                            os_list.append(x)
                                            time.sleep(0.5)
        
                                            for k in os_list:
                                                if "N" in k:
                                                    data=k
                                                    data_index_T = int(data.index('T'))
                                                    data_index_O = int(data.index('O'))
                                                    ps_list_T.append(data[data_index_T+1:data_index_T+5])
                                                    ps_list_O.append(data[data_index_O+1:data_index_O+7])
                
                                                    print("TestT1 : ",ps_list_T[0])
                                                    print("TestO1 : ",ps_list_O[0])
                                                
                                                    change_channel(8)
                                                    ser.write("\r".encode('utf-8'))
                                                    ser.write(data.encode('utf-8'))
                                                    time.sleep(0.5)
                
                                                    top_2=0
                                                
                                                    best=1
                                        except:
                                            pass

                                
                                    change_channel(8)
                                    os_list.clear()
                                    ps_list_T.clear()
                                    ps_list_O.clear()
                    
                                    os_list_2.clear()
                                    ps_list_T_2.clear()
                                    ps_list_O_2.clear()
                        
                                    os_list_3.clear()
                                    data_inform.clear()
                                    data=0
                                    cron = 0
                                    top = 0
                                    best = 0
                            
                                if "Ox2Check" in y:
                                    change_channel(2)
                                    best=1
                                    while(best):
                                        best_2 = 1
                                        while(best_2):
                                            try:
                                                y=ser.readline().decode('utf-8')
                                                os_list_2.append(y)
                                                time.sleep(0.5)
                                                for y in os_list_2:
                                                    if "N" in y:
                                                        data = y
                                                        data_index_T_2 = int(data.index('T'))
                                                        data_index_O_2 = int(data.index('O'))
                                                        ps_list_T_2.append(data[data_index_T_2+1:data_index_T_2+5])
                                                        ps_list_O_2.append(data[data_index_O_2+1:data_index_O_2+7])
                    
                                                        print("-----------------------------------------")
                                                        print("TestT2 : ",ps_list_T_2[0])
                                                        print("TestO2 : ",ps_list_O_2[0])
                                                    
                                                        change_channel(8)
                                                        ser.write("\r".encode('utf-8'))
                                                        ser.write(data.encode('utf-8'))
                                                        time.sleep(0.5)
                                                        cron = 1
                                                        best = 0
                                                        best_2 = 0
                                                    
                                            except:
                                                pass
                                    change_channel(8)
                                    os_list.clear()
                                    ps_list_T.clear()
                                    ps_list_O.clear()
                    
                                    os_list_2.clear()
                                    ps_list_T_2.clear()
                                    ps_list_O_2.clear()
                        
                                    os_list_3.clear()
                                    data_inform.clear()
                                    data=0
                                    cron = 0
                                    top = 0
                                    best = 0
                                if "FxCheck" in y:
                                    change_channel(3)
                                    cron = 1
                                    while(cron):
                                        ser.baudrate = 9600
                                        try :
                                            z.append(ser.readlines()[-1].decode('ascii'))
                                            z_2 = str(z[0])
                                            z.clear()
                                            os_list_3.append(z_2)
                                            time.sleep(0.5)
                                            for z_3 in os_list_3 :
                                                if "@T" in z_3:
                                                    data = z_2
                                                    data_inform = data.split(',')
                                                    data_inform_2 = float(data_inform[2])
                                                    data_inform_1 = float(data_inform[4].strip())
                                    
                                                    print("----------------------------------------")
                                                    print("TestFlx : " + str(data_inform_1))
                                                    print("TestTemp : " + str(data_inform_2))
                                                    print("----------------------------------------")
                                                    time.sleep(0.5)
                                                    ser.baudrate = 19200
                                                    change_channel(8)
                                                    ser.write("\r".encode('utf-8'))
                                                    ser.write(data.encode('utf-8'))
                                                    time.sleep(0.5)
                                                    cron = 0
                                                    top = 0
                                                
                                            change_channel(8) #조도센서3채널
                    
                                            best = 0
                                            os_list.clear()
                                            ps_list_T.clear()
                                            ps_list_O.clear()
                    
                                            os_list_2.clear()
                                            ps_list_T_2.clear()
                                            ps_list_O_2.clear()
                        
                                            os_list_3.clear()
                                            data_inform.clear()
                                            data=0
                
                
                                        except:        
                                            pass
                                        
                        except:
                            pass
        


                except IndexError:
                    continue                
                                
          
    except UnicodeDecodeError :
        continue
    
stir_motor_stop()

try:
    
    
    
    fileMatrix = []
    file_path = "config.txt"

    with open(file_path) as file :

        for lineContent in file: # Point.1
            fileMatrix.append(lineContent.strip('\n').split(' '))

    #print(fileMatrix)

    # 처음시간 정의

    now = datetime.now()
    now_compare = now.strftime("%Y-%m-%d %H:%M:%S")
    start_time = datetime.strptime(str(fileMatrix[2][1])+" "+str(fileMatrix[2][2]),"%Y-%m-%d %H:%M:%S")
    print("처음시작시간 : ",start_time)
    
    # 처음 시작시간까지의 차이
    delaytime = (start_time-now).seconds

    # 싸이클

    cyclecount = int(fileMatrix[0][1])+1

    # 로깅파일 정의

    logging_now = datetime.now()
    logging_now = now.strftime("%Y%m%d%H%M%S")

    # config파일 데이터를 로깅파일에 쓰기
    # 2차 배열을 txt 파일에 쓰는 형식

    f = open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','w')
    f.write("cycle "+str(cyclecount-1)+" " + str(fileMatrix[0][2]) + " " + str(fileMatrix[0][3]) + "\n")

    for i in range(5):
        f.write(str(fileMatrix[1][i]))
        f.write(" ")
    f.write("\n")
    f.close()

    for h in range(int(cyclecount-1)):
        f = open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','a')
        f.write(fileMatrix[h+2][0])
        f.write(" ")
        config_starttime = datetime.strptime(str(fileMatrix[h+2][1])+" "+str(fileMatrix[h+2][2]),"%Y-%m-%d %H:%M:%S")
        f.write(str(config_starttime))
        f.write(" ")
        f.write(fileMatrix[h+2][3])
        f.write(" ")
        f.write(fileMatrix[h+2][4])
        f.write("\n")
        f.close()

    f = open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','a')
    f.write("\n")
    f.write("No_Count Cycle Cycle_Count Measure_time_Day Measure_time_Hour Oxyzen_value_1 Oxyzen_value_2 Temp_value_1 Temp_value_2 THL_FLX THL_Temp Stir_pump_working Fill_pump_working\n")
    f.close()
except:
    pass


#main
while(startflag):   
    #f.close()  
    #f = open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','a')
    print('delay_time_sleep')
    delay_time_sleep()
    time.sleep(1)
    #start_mode()
    No_count = 0
    
    for i in range (cyclecount):
        Cycle_count = 0
        pump_ml = int(fileMatrix[i+2][4])
        Fill_pump_working = " X "
        stir_motor_start()
        time.sleep(1)
        mac = 1
        while(mac):
            print("----------------------------------------")
            now = datetime.now()
            now_compare = now.strftime("%Y-%m-%d %H:%M:%S") #지금 시간
            now_int = now.strftime("%Y%m%d%H%M%S")
            print("cycle : "+str(i+1)) #처음 출력이 1
            print("nowtime : "+str(now_compare)) #처음 출력이 프로그램 시작 설정시간하고 같아야한다
        
            start_compare = datetime.strptime(str(fileMatrix[i+2][1])+" "+str(fileMatrix[i+2][2]),"%Y-%m-%d %H:%M:%S") #프로그램시작 설정 시간
            time_diff = int((start_compare - now).seconds) #지금 사이클 남은시간
            
            
            try:
                next_starttime = datetime.strptime(str(fileMatrix[i+3][1])+" "+str(fileMatrix[i+3][2]),"%Y-%m-%d %H:%M:%S") #정해진 n번째 시작시간
                time_diff_2 = int((next_starttime - now).seconds)
                
            except IndexError:
                time_diff_2 = 200
                pass
            
            top=1
            
            if time_diff_2 <= 19: #사이클 종료 다음 사이클 준비
                mac = 0
                
            if(str(i+1) == cyclecount):
                mac=1
            print("next cycle "+str(i+2)+" starttime : "+str(next_starttime))
            print("time_diff2 : "+str(time_diff_2))
            print("----------------------------------------")           
            
            fill_motor_start(i,time_diff_2)
            motor_check()
            top = 1
            best = 1
            cron = 1
            while(top):
                change_channel(1) #산소센서 1채널
                top_2 = 1
                while(top_2):
                    try :
                        ser.close()
                        ser.open()
                        x = ser.readline().decode('utf-8')
                        os_list.append(x)
                        #time.sleep(0.5)
                        
                        for k in os_list :
                            if "N" in k:
                                data = k
                                data_index_T = int(data.index('T'))
                                data_index_O = int(data.index('O'))
                                ps_list_T.append(data[data_index_T+1:data_index_T+5])#['2999', '3012']
                                ps_list_O.append(data[data_index_O+1:data_index_O+7])#['2454', '2474']
                
                                print("T1 : ",ps_list_T[0])
                                print("O1 : ",ps_list_O[0])
                    
                                top_2 = 0
                                change_channel(2) #산소 센서2 채널
                                best = 1
                    
                    except :
                        pass
    
    
    
    
    
                while(best):
                    best_2 = 1
                    while(best_2):
                        try:
                            y = ser.readline().decode('utf-8')        
                            os_list_2.append(y)
                            #time.sleep(0.5)
                            for y in os_list_2 :
                                if "N" in y:
                                    data = y
                                    data_index_T_2 = int(data.index('T'))
                                    data_index_O_2 = int(data.index('O'))
                                    ps_list_T_2.append(data[data_index_T_2+1:data_index_T_2+5])#['2999', '3012']
                                    ps_list_O_2.append(data[data_index_O_2+1:data_index_O_2+7])#['2454', '2474']
                        
                                    print("----------------------------------------")
                                    print("T2 : ",ps_list_T_2[0])
                                    print("O2 : ",ps_list_O_2[0])
                                    cron = 1
                                    best = 0
                                    best_2 = 0
                                    change_channel(3) #조도센서3채널
                        except:
                            pass
        
                            
                    while(cron):
                        ser.baudrate = 9600
                        try :
                            z.append(ser.readlines()[-1].decode('ascii'))
                            z_2 = str(z[0])
                            z.clear()
                            os_list_3.append(z_2)
                            time.sleep(0.5)
                            for z_3 in os_list_3 :
                                if "@T" in z_3:
                                    data = z_2
                                    data_inform = data.split(',')
                                    data_inform_2 = float(data_inform[2])
                                    data_inform_1 = float(data_inform[4].strip())
                                    
                                    print("----------------------------------------")
                                    print("Flx : " + str(data_inform_1))
                                    print("Temp : " + str(data_inform_2))
                                    print("----------------------------------------")
                                    time.sleep(0.5)
                                    ser.baudrate = 19200
                                    time.sleep(0.5)
                                    cron = 0
                                    top = 0
                
                            best = 0
                
                
                        except:        
                            pass

                Cycle_count += 1
                No_count += 1
                f=open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','a')
                f.write(str(No_count)+" "+str(i+1)+" "+str(Cycle_count)+" "+str(now_compare)+" "+str(float(int(ps_list_O[0])/100))+" "+
                str(float(int(ps_list_O_2[0])/100))+" "+str(float(int(ps_list_T[0])/100))+" "+str(float(int(ps_list_T_2[0])/100))+" "+
                str(data_inform_1)+" "+str(data_inform_2)+" "+str(stir_2[0])+" "+str(fill_2[0]))
                f.write("\n")
                f.close()
                f = open("/home/pi/logging_data/logging_data"+str(logging_now)+'.txt','a')
                
                os_list.clear()
                ps_list_T.clear()
                ps_list_O.clear()
                    
                os_list_2.clear()
                ps_list_T_2.clear()
                ps_list_O_2.clear()
                        
                os_list_3.clear()
                data_inform.clear()
                time.sleep(0.5)
                          
            
            data=0

    f.close()
    startflag = 0







