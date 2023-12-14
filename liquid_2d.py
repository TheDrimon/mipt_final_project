import pygame as pg
import numpy as np
import GUI

def Field_init():
    global NL, idxs, cxs, cys, weights
    global F
    NL = 9
    idxs = np.arange(NL)
    cxs = np.array([-1, 0, 1,
				    -1, 0, 1,
				    -1, 0, 1])
    cys = np.array([1, 1, 1,
				    0, 0, 0,
				    -1,-1,-1])
    weights = np.array([1/36, 1/9, 1/36,
					    1/9,  4/9, 1/9,
					    1/36, 1/9, 1/36])
    
    #####v = np.float64(np.zeros((N*He//Wi,N,2)))
    Nx, Ny = N*He//Wi, N

    # Начальные условия
    global cylinder, rho0, tau
	            
    rho0 = 10 # average density
    tau = 1 # collision timescale
	
    F = np.ones((Ny,Nx,NL)) * rho0 / NL
	
    np.random.seed(42)
	
    F += 0.01*np.random.randn(Ny,Nx,NL)
	
    X, Y = np.meshgrid(range(Nx), range(Ny))
	
    F[:,:,1] += 2*(1+0.2*np.cos(2*np.pi*X/Nx*4))
	
    rho = np.sum(F,2)
    for i in idxs:
        F[:,:,i] *= rho0 / rho


    cylinder = (X - Nx/2)**2 + (Y - Ny/4)**2 < (Nx/4)**2 # Cylinder boundary
	
    global display
    display.update(F, cylinder)


def init():
	# GUI init <--
    global N, screen, Wi, He, b
    global mode, play
    global Buttons, display
    
    play = 0
    mode = "draw"  # draw select del 
    Wi, He = 1080,360
    N = 324
    
    
    
    pg.init()
    b = 30
    screen = pg.display.set_mode((Wi,He + b)) 
    
    Buttons = [GUI.Button(screen, 0,He, b*2,b, "reset"),
			   GUI.Switch(screen, b*2.1*2,He, b*2,b, ["draw","select","del"]),
			   GUI.Switch(screen, b*2.1,He, b*2,b, ["play","pause"])]
    display = GUI.Display(screen, 0,0, Wi,He)
	
    # MODEL init <--
    Field_init()
	
    

def step_calc():
		global cylinder, F
		global display
		#print(it)

		# Drift
		for i, cx, cy in zip(idxs, cxs, cys):
			F[:,:,i] = np.roll(F[:,:,i], cx, axis=1)
			F[:,:,i] = np.roll(F[:,:,i], cy, axis=0)


		# Set reflective boundaries
		bndryF = F[cylinder,:]
		bndryF = bndryF[:,[-1,-2,-3,-4,-5,-6,-7,-8,0]]


		# Calculate fluid variables
		rho = np.sum(F,2)
		ux  = np.sum(F*cxs,2) / rho
		uy  = np.sum(F*cys,2) / rho


		# Apply Collision
		Feq = np.zeros(F.shape)
		for i, cx, cy, w in zip(idxs, cxs, cys, weights):
			ss = (cx*ux+cy*uy)
			Feq[:,:,i] = rho * w * ( 1 + 3*ss + 9*ss**2/2 - 3*(ux*ux+uy*uy)/2 )

		F += -(1.0/tau) * (F - Feq)

		# Apply boundary
		F[cylinder,:] = bndryF


		display.update(F, cylinder)
			
	
def interract(press, pos):
	global mode, Buttons, play
	
	x,y = pos[:2]
	if 0 < x < Wi:
		if 0 < y < He:
			# работа с полем
			print(pos)
			if type == "draw":
				pass
			if type == "select":
				pass
			elif type == "del":
				pass
        
		elif He < y < He + b:
			for Bt in Buttons: # переключение кнопок
				if Bt.pos[0] < x < Bt.pos[0] + Bt.size[0]:
					Bt.press(press)
		
		if press == 0:
			for Bt in Buttons: # сброс кнопок
				Bt.reset()
		
	# реакции кнопок
	if Buttons[0].active:
		Field_init()
		Buttons[0].active = 0
	if Buttons[2].active:
		if Buttons[2].state == 0:
			play = 0
		elif Buttons[2].state == 1:
			play = 1
		Buttons[2].active = 0
		
			
	
	
	

    

def draw():
	screen.fill((0,0,0))

	display.draw()# отрисовка по скорости кручения
	
	for i in Buttons:# интерфейс
		i.draw()
		
	pg.display.update()


def main():
	init()
	
	clock = pg.time.Clock()
	RUN = True
	
	while RUN:
		if play:
			step_calc()
		
		draw()

		clock.tick(60)
            
		for event in pg.event.get():
			if event.type == pg.QUIT:
				RUN = False
				
			elif event.type == pg.MOUSEBUTTONDOWN:
				interract(1, event.pos)
				
			elif event.type == pg.MOUSEBUTTONUP:
				interract(0, event.pos)
			
			elif event.type == pg.MOUSEMOTION:
				pass


if __name__ == "__main__":
    main()