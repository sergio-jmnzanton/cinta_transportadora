import time
import speech_recognition as sr
import RPi.GPIO as GPIO
import mysql.connector
import datetime
import requests

#CONEXION CON MYSQL

mydb = mysql.connector.connect(
	user='admin',
	password='root',
	host='127.0.0.1',
    database='cinta'
)

mycursor = mydb.cursor()

r = sr.Recognizer()
r.pause_threshold = 0.5
m = sr.Microphone()
r.operation_timeout = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) #PIN del buzzer
GPIO.setup(16, GPIO.IN) #PIN del sensor IR

texto = 0
pin_ldr= 7 #PIN del fotoresistor


with m as source:
    r.adjust_for_ambient_noise(source)  #Ajustar el ruido ambiente al microfono (solo se realiza una vez al principio)

def callback(recognizer, audio): #Funcion ejecutada en un hilo secundario (background thread) que escucha activamente el microfono
    
    try:
        global texto
        texto = recognizer.recognize_google(audio, language='es-ES')
        print("Has dicho " + texto)
    except sr.UnknownValueError:
        print("No se reconocio la orden")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

def rc_time(): #Obtener lectura analogica del fotoresistor.

    count = 0

    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, GPIO.LOW)
    time.sleep(0.5)

    GPIO.setup(7, GPIO.IN)

    while (GPIO.input(7) == GPIO.LOW):
        count += 1

    return count

def iniciar_cinta(): #Funcion que pone en marcha la cinta
    
    requests.post("https://maker.ifttt.com/trigger/cinta_iniciada/with/key/bdXiQ8Ftr3DpQ0Igri61H_") #Implementación de IFTTT
    
    inicial = int(round(time.time()*1))
    diferencia = 0
    numPieza = 0
    
    GPIO.setup(15, GPIO.OUT) #Activar el motor
    p = GPIO.PWM(15, 50) #Enviar 50 pulsos al motor
    p.start(5)
    
    while diferencia<15 or texto!='parar cinta':
          
        
        i = GPIO.input(16) #Sensor
        
        actual = int(round(time.time()*1))
        diferencia = actual-inicial
        
        x = datetime.datetime.now()
        x = x.strftime('%Y-%m-%d %H:%M:%S')
        
        if i == 0: #Si detecta objeto
            
            numPieza+=1
            
            inicial = int(round(time.time()*1))
            
            GPIO.output(11, True) #Sonar buzzer
            time.sleep(0.1)
            GPIO.output(11, False) #Apagar buzzer
                
            time.sleep(0.1)
                
            if rc_time()>100:
                print('Pieza grande')
                tamano = "grande"
                sql = "INSERT INTO objetos VALUES (%s, %s, %s)"
                val = [numPieza, tamano, x]
                print(val)
                mycursor.execute(sql, val)
                mydb.commit()
                print(mycursor.rowcount, "fila(s) insertadas.")
        
            else:
                print('Pieza pequena')
                tamano = "pequena"
                sql = "INSERT INTO objetos VALUES (%s, %s, %s)"
                val = [numPieza, tamano, x]
                print(val)
                mycursor.execute(sql, val)
                mydb.commit()
                print(mycursor.rowcount, "fila(s) insertadas.")
      
    GPIO.setup(15, GPIO.IN) 
                
stop_listening = r.listen_in_background(m, callback, phrase_time_limit=3)

while True: 
    time.sleep(0.1)
    if texto == 'iniciar cinta':
       iniciar_cinta()
       texto = 0
       GPIO.cleanup() #Limpiar GPIO

