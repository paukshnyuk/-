#include <8051.h>

#define frequency 6000

bit Mode;

interrupt void ChangeMode(void)
{
	if (Mode == 0)	{ Mode = 1; }
	else 			{ Mode = 0; }

	switch(Mode)
	{
		case 0:		// 12V and -12V (Standart)
		P0 = 0;
		P00 = 1;
		P01 = 1;
		break;

		case 1:		// 16V and -8V (Alternative)
		P0 = 0;	
		P02 = 1;
		P03 = 1;	
		break;
	}
}

void main()
{
	Mode = 0;

	IT0 = 0;
	EX0 = 1;
	EA = 1;

	P0 = 0;	
	P00 = 1;
	P01 = 1;
	
	while(1)
	{
		P36 = 1;	
		P2 = P1;
		while(P37) { /* Preobrazovanie */ }
		P36 = 0;
	}
}

