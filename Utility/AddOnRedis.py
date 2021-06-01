import redis

# Questo programma serve ad aggiungere chiavi al database
# chiavi e valori vengono prese dal file di testo in questa cartella

r = redis.Redis(host='localhost', port=6379, db=0)

path ='/Users/gab/Desktop/STM Mac/VSCODE/Progetto/ListaChiavi.txt'
data = open( path , 'r')

valori = data.read().split('\n')

data.close()

if len(valori) == 1 :
    print("File vuoto")
else :
    for i in valori:
        c=0
        if i[:1] != '#':

            while i[c] != ' ':
                c=c+1
            
            if r.exists(i[:c])==0 :
                print('Inserisco in '+i[:c])
                for j in range(6):
                   print(r.rpush(i[:c] , i[ (c+2)+j*5:(c+6)+j*5]))

