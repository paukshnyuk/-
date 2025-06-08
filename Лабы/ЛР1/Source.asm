.686
.model flat, stdcall

.stack 100h

.data

X dw 15
Y dw 79
Z dw 81
M dw ?

.code
ExitProcess PROTO STDCALL : DWORD
Start :

MOV AX, [X]
ADD AX, [Y]

MOV CX, 4
DIV CX

MOV BX, [Z]
SUB BX, [Y]
SUB BX, [X]

OR AX, BX

MOV [M], AX

exit:
Invoke ExitProcess, 1
End Start
