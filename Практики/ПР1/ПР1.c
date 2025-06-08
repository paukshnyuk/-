#include <8051.h>

void main()
{
    int i;
    char xdata *ptr;
    char test, nabor;

    P1 = P1 & ~0x01; 

    nabor = 0x33; 
    ptr = (char xdata *) 0x240; 

    for(i=0; i<1024; i++) 
    {
        *ptr = nabor;
        test = *ptr;
        if(test != nabor)
        {
            P1 = P1 | 0x01; 
            break;
        }
        ptr++;
    }
    //while(1); 
}
