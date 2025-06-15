.686
.model flat, stdcall
.stack 100h

ExitProcess PROTO STDCALL :DWORD

.data
inputStr db '-123.67',0 

result dd 0              
ten real8 10.0           
frac_digits dd 0         
fpu_result dq 0.0        
temp_digit dd 0          

.code
Start:
    finit                    

    lea esi, inputStr
    mov eax, 0               

    mov al, [esi]
    mov bl, 0                

    cmp al, '+'
    je  plus_sign
    cmp al, '-'
    je  minus_sign
    cmp al, '0'              
    jb  fail_empty_or_invalid_char 
    cmp al, '9'
    jbe int_part_start       
    jmp fail_empty_or_invalid_char 

plus_sign:
    mov bl, 2                
    inc esi                  
    jmp int_part_start

minus_sign:
    mov bl, 1                
    inc esi                  
    jmp int_part_start

int_part_start:
    mov al, [esi]
    cmp al, 0
    je fail_no_digits        

    mov cl, 0                

    fldz                     

digits_before_dot:
    mov al, [esi]            

    cmp al, 0                
    je fail_no_dot           

    cmp al, '.'              
    je dot_found

    cmp al, '0'              
    jb fail_invalid_char     
    cmp al, '9'
    ja fail_invalid_char     

    fmul qword ptr [ten]     

    sub al, '0'              
    movzx eax, al            
    mov [temp_digit], eax    

    fild dword ptr [temp_digit] 
    faddp st(1), st(0)       

    inc esi                  
    mov cl, 1                
    jmp digits_before_dot    

dot_found:
    cmp cl, 1                
    jne fail_no_digits_before_dot 
    inc esi                  

    mov al, [esi]
    cmp al, 0
    je fail_no_digits_after_dot 

    mov cl, 0                
    mov dword ptr [frac_digits], 0 

    fldz                     

digits_after_dot:
    mov al, [esi]            

    cmp al, 0                
    je check_end             

    cmp al, '0'              
    jb fail_invalid_char     
    cmp al, '9'
    ja fail_invalid_char     

    fmul qword ptr [ten]     

    sub al, '0'              
    movzx eax, al            
    mov [temp_digit], eax    

    fild dword ptr [temp_digit] 
    faddp st(1), st(0)       

    inc esi                  
    inc dword ptr [frac_digits] 
    mov cl, 1                
    jmp digits_after_dot     

check_end:
    cmp cl, 1                
    jne fail_no_digits_after_dot 

    mov ecx, [frac_digits]   
    cmp ecx, 0
    je only_integer_fpu      

    fld1                     
    mov edx, ecx             
pow_loop:
    cmp edx, 0
    je pow_done
    fmul qword ptr [ten]     
    dec edx
    jmp pow_loop
pow_done:
    fdivp st(1), st(0)       
    faddp st(1), st(0)       

    jmp check_sign

only_integer_fpu:
    nop

check_sign:
    cmp bl, 1                
    jne save_result          
    fchs                     

save_result:
    fstp qword ptr [fpu_result] 
    mov eax, 1               
    mov [result], eax
    jmp done

fail_empty_or_invalid_char:
fail_no_digits:
fail_no_dot:
fail_invalid_char:
fail_no_digits_before_dot:
fail_no_digits_after_dot:
    mov eax, 0               
    mov [result], eax

done:
    finit

    Invoke ExitProcess,0
end Start