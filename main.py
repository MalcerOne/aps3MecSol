from enum import IntEnum
from funcoesTermosol import *
import numpy as np

def condicoesContorno(matrizGlobal, condicoes):
    if np.shape(matrizGlobal)[1] != 1:
        return np.delete(np.delete(matrizGlobal, list(condicoes[:,0].astype(int)),axis=0), list(condicoes[:,0].astype(int)),axis=1)
    else:
        return np.delete(matrizGlobal, list(condicoes[:,0].astype(int)), axis = 0)

def main():
    nn, N, nm, Inc, nc, F, nr, R = importa('entrada-grupo1.xlsx')
    
    E = Inc[0,2]
    A = Inc[0,3]

    plota(N, Inc)

    # Definir a matriz de conectividade
    matrizConectividade = np.zeros((nm, nn))

    for col in range(len(Inc[:,0])):
        matrizConectividade[int(Inc[:,0][col] -1), col] = -1
        matrizConectividade[int(Inc[:,1][col] -1), col] = 1
        
    #print(f"Matriz de conectividade: \n{matrizConectividade}")

    # Calcular a matriz de rigidez de cada elemento
    # Montar a matriz de rigidez global [Kg] da trelica
    matrizMembros = N @ matrizConectividade # multiplicacao matricial `@`
    comprimento = np.zeros((np.shape(matrizMembros)[1], 1))
    numeroElementos = np.shape(matrizMembros)[1]

    #print(matrizConectividade)

    for col in range(numeroElementos):
        comprimento[col] = np.linalg.norm(matrizMembros[:,col])
    
    colunas_membros = np.shape(matrizMembros)[1]
    linhas_membros  = np.shape(matrizMembros)[0]
    matrizRigidez = []
    matrizRigidezGlobal = np.zeros((nn*2, nn*2))
    S = np.zeros((2, 2))

    for col in range(colunas_membros):
        m = (matrizMembros[:, col]).reshape(linhas_membros, 1)
        m_transpose = np.transpose(m)

        S = ((E * A) / comprimento[col]) * ((m @ m_transpose) / (np.linalg.norm(m)) ** 2)
        conectividade = (matrizConectividade[:, col]).reshape(np.shape(matrizConectividade)[0],1)
        conectividade_transpose = np.transpose(conectividade)

        rigidez = np.kron((conectividade @ conectividade_transpose), S)
        matrizRigidez.append(rigidez)
        matrizRigidezGlobal += rigidez

    # Aplicar condicoes de contorno
    mRigidezGlobalCC = condicoesContorno(matrizRigidezGlobal, R)
    vetorGlobalForcasCC = condicoesContorno(F, R)

    # Aplicar um metodo numerico para resolver o sistema de equacoes e obter os deslocamentos nodais
    colunas_rigidez = np.shape(mRigidezGlobalCC)[1]
    linhas_rigidez = np.shape(mRigidezGlobalCC)[0]
    
    x = np.zeros((linhas_rigidez,1)) # chute inicial
    xnew = np.zeros((linhas_rigidez, 1)) 
    tolerancia = 1e-10
    p = 100 # maximo de iteracoes
    
    for i in range(p):
        # Método de Jacobi
        for l in linhas_rigidez:
            xnew[l] = (vetorGlobalForcasCC[l] - xnew[l]) / mRigidezGlobalCC[l][l]
        
        # Erro
        erro = max(abs((xnew-x)/xnew))
        
        # Atualizar
        x = np.copy(xnew)
        
        if erro <= tolerancia:
            break

    # Determinar a deformacao em cada elemento
    # Criar matriz de angulos
    matrizTrigo = np.zeros((numeroElementos, 4))

    for elemento in range(numeroElementos):
        matrizTrigo[elemento, 0] = -matrizConectividade[elemento, 2] # cos
        matrizTrigo[elemento, 1] = -matrizConectividade[elemento, 3] #sen
        matrizTrigo[elemento, 2] = (matrizMembros[0, elemento])/comprimento[elemento] # cos
        matrizTrigo[elemento, 3] = (matrizMembros[1, elemento])/comprimento[elemento] # sen

    # Criar matriz de deslocamentos
    matrizDeslocamentos = np.zeros((len(R) + len(x), 1))
    cond = list(R[:,0].astype(int))
    contador = 0

    for deslocamento in range(len(matrizDeslocamentos)):
        if deslocamento not in cond:
            matrizDeslocamentos[deslocamento] = x[contador]
            contador = contador + 1
    
    deformacoes = np.zeros((len(comprimento), 1))

    for item in range(len(comprimento)):
        deformacoes.append((1/comprimento[item]) * (matrizTrigo[item] @ matrizDeslocamentos[item]))

    # Determinar a tensao em cada elemento
    tensao = E * deformacoes

    # Determinar as reacoes de apoio
    reacoesDeApoio = (matrizRigidezGlobal @ matrizDeslocamentos)[cond]

    # Determinar as forcas internas
    forcasInternas = A * tensao

    # Gera um arquivo de output com as reacoes de apoio, matriz de deslocamentos, deformacoes, forcas internas e tensao
    geraSaida("output", reacoesDeApoio, matrizDeslocamentos, deformacoes, forcasInternas, tensao)

if __name__ == '__main__':
    main()