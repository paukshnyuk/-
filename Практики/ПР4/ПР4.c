#include <8051.h>

void msec(int x) 
{
    while(x-- > 0) 
    {
        TH0 = (-1000) >> 8;    
        TL0 = -1000;           
        TR0 = 1;                
        while(TF0 == 0);        
        TF0 = 0;                
        TR0 = 0;                
    }
}

void main() 
{
    TMOD = 0x01;   
    while(1)
    {
        P1 = 0x88;  
        msec(2); 
        P1 = 0x06;  
        msec(5); 
        P1 = 0x60; 
        msec(8); 
        P1 = 0x11;  
        msec(2); 
    }
}
