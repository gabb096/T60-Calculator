# Progetto Sistemi Operativi e Reti
# Leva Gabriele #
import tornado.ioloop 
import tornado.web
import tornado
import redis
from math import log, sqrt, pow
from matplotlib import pyplot as plt
from datetime import datetime, date

class MainHandler(tornado.web.RequestHandler): 
    
    def get(self):
        self.render('index.html')
        

class ResultHandler(tornado.web.RequestHandler): 
    
    def post(self):
        
        r = redis.Redis(host='localhost', port=6379, db=0)  # Connection to Redis
        CAM = [0.0,0.0,0.0,0.0,0.0,0.0]                     # Absorption coefficients according to frequency 
        T = [0.0,0.0,0.0,0.0,0.0,0.0]                       # Reverberation times based on frequency 
        T60 = 0.0                                           # Average reverberation time
        freq = [125,250,500,1000,2000,4000]                 # Frequencies considered
        
        w = float(self.get_argument('Width'))/100           # Width  in meters
        h = float(self.get_argument('Height'))/100          # Height in meters
        d = float(self.get_argument('Depth'))/100           # Depth  in meters
        Costante = -0.16

        # Considering the room as a simple parallelepiped
        Volume = float(w * d * h) 
        STot = float(2*(w*d + w*h + d*h)) # Total surface area
        
        # Perimeter_wall        
        try:   
            val = self.get_argument('Perimeter_wall') 
            for i in range(6):
                CAM[i] = CAM[i]+float(str(r.lrange(val, i, i))[3:7])*2*h*(d+w)  # 2*h*(d+w) = Side surface
                # r.lrange(val, i, i) returns something like this [b'0.12'],
                # that's why we do str(r.lrange(val, i, i))[3:7]
                # and then converting it to float 
        except: 
            self.write("There was a problem in calculating the coefficient of the perimeter wall<br>")
            self.write("The chosen material is not present in our database<br>")
            self.write("Try changing it to something similar among the suggested<br>")
        
        # Ceiling
        try:   
            val = self.get_argument('Ceiling') 
            for i in range(6):
                CAM[i] = CAM[i] + float(str(r.lrange(val, i, i))[3:7])*d*w
        except: 
            self.write("There was a problem in calculating the coefficient of the Ceiling<br>")
            self.write("The chosen material is not present in our database<br>")
            self.write("Try changing it to something similar among the suggested<br>")
        
        # Floor 
        try:
            val = self.get_argument('Floor')
            for i in range(6): 
                CAM[i] = CAM[i] + float(str(r.lrange(val, i, i))[3:7]) *(d*w)
        except: 
            self.write("There was a problem in calculating the coefficient of the Floor<br>")
            self.write("The chosen material is not present in our database<br>")
            self.write("Try changing it to something similar among the suggested<br>")
        
        # Windows
        if self.get_argument('Windows') != '':
            Num = int(self.get_argument('Windows')) # Number of windows
            for i in range(6):
                red = str(r.lrange('Finestre_Chiuse', i, i))[3:7]
                CAM[i] = CAM[i] + float(red)*Num*0.5074 
            STot = STot + Num*0.5074
            # 0.5074 m^2 is the average surface area of a window with a single sash
        
        # Doors
        if self.get_argument('Doors') != '':
            Num = int(self.get_argument('Doors')) # Number of doors
            for i in range(6):
                red = r.lrange('Porta_In_Legno', i, i)
                CAM[i] = CAM[i] + (float(str(red)[3:7]))*Num*1.51
            STot = STot + Num*1.51
            #  1.51 m^2 is the average surface area of a door
        
        # Objects
        for j in range(6): 
            try:    
                if  self.get_argument('obj' + str(j)) != '' and  self.get_argument('dim' + str(j)) != '' :
                    ogg = self.get_argument('obj' + str(j)) # Kind of object
                    dim = self.get_argument('dim' + str(j)) # Dimension of the object
                    for i in range(6):
                        red = str(r.lrange(ogg, i, i))[3:7] 
                        CAM[i] = CAM[i] + (float(red))*float(dim)/100
                        STot = STot + float(dim)/100
            except: 
                self.write("There was a problem in calculating the coefficient of the furniture<br>")
                self.write("The chosen material is not present in our database<br>")
                self.write("Try changing it to something similar among the suggested<br>")
        
        self.write('<h3>The Absorption Coefficients are : </h3>')
        
        for k in range(6) :
            CAM[k]=CAM[k]/STot
            if CAM[k] <1 :
                T[k]  = (Costante*Volume)/(log(1.0 - CAM[k])*STot)

                self.write(str(CAM[k])[:4] + " at " +
                            str(freq[k]) + " Hz and the reverberation time is " + 
                            str(T[k])[:4] + ' seconds<br>')
                T60 = T60 + T[k] 
        
        self.write("<h4>The volume of the environment is : "+str(Volume)[:4]+ "m^3</h4>")
        self.write('<h4>The total surface area is : '+str(STot)[:4]+' m^2</h4>')
        self.write('The average reverberation time is : '+str(T60/6)[:4]+' second <br>')        

        path = "/Users/gab/Desktop/STM_Mac/VSCODE/TESI/img/"
        time = "_"+date.today().strftime("%d-%m-%Y")+"_"+datetime.now().time().strftime("%H%M%S")
        plt.figure(1)
        plt.plot(freq, T, linewidth=3)
        plt.title('Reverb Time')
        plt.xlabel('Frequencies in Hz')
        plt.ylabel('Time in s')
        path1 = path+"Plot"+time+".png"
        plt.savefig(path1)
        
        self.write(f'<img src="http://localhost:8888/static/{path1}" width="500" height="300" >')
        
        # calculating the stationary waves
        modes = {}
        r=10
        for k1 in range(r) :
            for k2 in range(r) :
                for k3 in range(r) :
                    m = 345/2 * sqrt( pow(k1/w,2) + pow(k2/h,2) + pow(k3/d,2))
                    if m not in modes :
                        if m < 500 :
                            modes.update({ int(m) : 1 })
                    else :
                        modes[m]=modes.get(m)+1
        
        x,y = [],[]
        x = list(modes.keys())
        x.sort()
        
        self.write("<br>These are the frequencies that can create stationary waves<br>")
        
        for i in x:
            y.append(modes.get(i))
        
        plt.figure(2)
        plt.bar(x[1:],y[1:], 5)
        plt.title('Stationary Waves')
        plt.xlabel('Frequencies in Hz')
        plt.ylabel('Repetitions')
        path2 = path+"Bar"+time+".png"
        plt.savefig(path2)
        
        self.write(f'<img src="http://localhost:8888/static/{path2}" width="500" height="300" >')
        self.write(f'<br>List of frequencies in the graph<br>')
        self.write("Frequencies with more than one repetition<br>")
        
        c=0
        for i in x[1:] :
            if modes.get(i)>1:
                c=c+1
                self.write(f'{modes.get(i)} volte a {str(i)} Hz, ')
        
        self.write("<br>Frequencies with a single repetition<br>")
        
        for i in x[1:] :
            c=c+1
            self.write(f'{str(i)} Hz, ')
            if c%9==0:
                self.write("<br>")
        if c==0:
            self.write("<Great, no standing waves!<br>")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/result", ResultHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': "/Users/gab/Desktop/STM_Mac/VSCODE/TESI/img/"})
        ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888) 
    tornado.ioloop.IOLoop.current().start()
