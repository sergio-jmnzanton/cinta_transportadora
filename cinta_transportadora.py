import time 
import speech_recognition as sr #PAQUETE PARA EL RECONOCIMIENTO DE VOZ
import RPi.GPIO as GPIO
import mysql.connector #PARA EL USO DE MySQL EN Python
import datetime #PARA DETENER LA CINTA TRANSCURRIDOS 10 SEGUNDOS
import requests #PARA EL USO DE IFTTT (Webhooks + SMS)

#CONEXION CON MYSQL
mydb = mysql.connector.connect(
	user='admin',
	password='root',
	host='127.0.0.1',
    	database='cinta'
)

mycursor = mydb.cursor()


#CONTROLES DEL PAQUETE SpeechRecognition
r = sr.Recognizer()
r.pause_threshold = 0.5
m = sr.Microphone()
r.operation_timeout = 1

#SETUP DEL GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) #PIN del buzzer
GPIO.setup(16, GPIO.IN) #PIN del sensor IR

texto = 0 #VARIABLE DONDE SE GUARDA EN FORMATO STRING LA ORDEN DE VOZ INTRODUCIDA
pin_ldr= 7 #PIN del fotoresistor


with m as source:
    r.adjust_for_ambient_noise(source)  #Ajustar el ruido ambiente al microfono (solo se realiza una vez al principio)

def callback(recognizer, audio): #FUNCION EJECUTADA EN UN HILO SECUNDARIO (background thread) QUE ESCUCHA ACTIVAMENTE EL MICROFONO
    
    try:
        global texto
        texto = recognizer.recognize_google(audio, language='es-ES')
        print("Has dicho " + texto)
    except sr.UnknownValueError:
        print("No se reconocio la orden")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e)) #EXCEPCION POR DEFECTO DE SpeechRecognition EN CASO DE NO HABER CONEXION A INTERNET

	def rc_time(): #OBTENCION DE LECTURA ANALOGICA DEL FOTORRESISTOR LDR
    
    count = 0

    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, GPIO.LOW)
    time.sleep(0.5)

    GPIO.setup(7, GPIO.IN)

    while (GPIO.input(7) == GPIO.LOW):
        count += 1

    return count

def iniciar_cinta(): #FUNCION QUE PONE EN MARCHA LA CINTA
    
    requests.post("https://maker.ifttt.com/trigger/cinta_iniciada/with/key/bdXiQ8Ftr3DpQ0Igri61H_") #IMPLEMENTACION DE IFTTT (MANDA UN SMS INFORMATIVO A UN MOVIL CUANDO SE INICIA LA CINTA)
    
    inicial = int(round(time.time()*1)) #SEGUNDOS
    diferencia = 0
    numPieza = 0
    
    GPIO.setup(15, GPIO.OUT) #ACTIVACION DEL MOTOR DE LA CINTA
    p = GPIO.PWM(15, 50) #ENVIO DE 50 PULSOS AL MOTOR
    p.start(5)
    
    while diferencia<15 or texto!='parar cinta': #SE DETIENE CON LA ORDEN 'parar cinta' O CUANDO PASAN 15 SEGUNDOS SIN DETECTAR UN OBJETO
          
        
        i = GPIO.input(16) #Sensor
        
        actual = int(round(time.time()*1))
        diferencia = actual-inicial
        
        x = datetime.datetime.now()
        x = x.strftime('%Y-%m-%d %H:%M:%S') #FORMATEO DE LA FECHA DE Python PARA QUE CUADRE EN MySQL
        
        if i == 0: #SI DETECTA OBJETO
            
            numPieza+=1 #INCREMENTA EL NUMERO DE PIEZA (ID)
            
            inicial = int(round(time.time()*1))
            
            GPIO.output(11, True) #HACE SONAR EL BUZZER POR 0.1 SEGUNDOS
            time.sleep(0.1)
            GPIO.output(11, False) #APAGA EL BUZZER
                
            time.sleep(0.1)
                
            if rc_time()>100: #LECTURA ANALOGICA DEL LDR (EL EMISOR LASER APUNTA CONSTANTEMENTE AL LDR)
                print('Pieza grande')
                tamano = "grande"
                sql = "INSERT INTO objetos VALUES (%s, %s, %s)" 
                val = [numPieza, tamano, x]
                print(val)
                mycursor.execute(sql, val) #INSERCION DE UN REGISTRO EN LA BASE DE DATOS
                mydb.commit()
                print(mycursor.rowcount, "fila(s) insertadas.")
        
            else:
                print('Pieza pequena')
                tamano = "pequena"
                sql = "INSERT INTO objetos VALUES (%s, %s, %s)"
                val = [numPieza, tamano, x]
                print(val)
                mycursor.execute(sql, val) #INSERCION DE UN REGISTRO EN LA BASE DE DATOS
                mydb.commit()
                print(mycursor.rowcount, "fila(s) insertadas.")
      
    GPIO.setup(15, GPIO.IN) 
                
stop_listening = r.listen_in_background(m, callback, phrase_time_limit=3) #EL PROGRAMA ESTA CONSTANTEMENTE ESCUCHANDO ORDENES DE VOZ, SEA CUAL SEA EL PUNTO EN EL QUE SE ENCUENTRE EL PROGRAMA

while True: #EQUIVALENTE A LA FUNCION MAIN

    time.sleep(0.1)
    if texto == 'iniciar cinta': #SI SE INTRODUCE LA ORDEN 'iniciar cinta' LLAMA A LA FUNCION 'iniciar_cinta()'
       iniciar_cinta()
       texto = 0
       GPIO.cleanup() #LIMPIAR GPIO AL ACABAR

