#include <8051.h>

void delay(void)
{
    unsigned int i;
    for(i=0; i<10; i++);
}

void lcd_cmd(unsigned char cmd)
{
    P0 = cmd;
    P2 = 0x1;
    P2 = 0x0;
}

void lcd_data(unsigned char dat)
{
    P0 = dat;
    P2 = 0x3;
    P2 = 0x2;
}

void lcd_print(unsigned char *str)
{
	
    while(*str)
    {
      lcd_data(*str++);
    }
}

void main()
{
	unsigned char str1[8] = {175, 178, 171, 175, 172, 171, 175, 162};
    unsigned char swap = 0;
	
    unsigned char str2[6] = {173, 169, 182, 160, 169, 172};

    lcd_cmd(0x38);
    lcd_cmd(0x0C);
    lcd_cmd(0x01);
    delay();

    while(1)
    {
        lcd_cmd(0x01);
        delay();

        if(swap == 0)
        {
            lcd_cmd(0x80);
            lcd_print(str1);
			lcd_cmd(0xC0 + 24); 
            lcd_print(str2);
        }
        else
        {
            lcd_cmd(0x80);
            lcd_print(str2);
			lcd_cmd(0xC0 + 22); 
            lcd_print(str1);
        }
		delay();   
        delay();
		swap = !swap;
    }
}
