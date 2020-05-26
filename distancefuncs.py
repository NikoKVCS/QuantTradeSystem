import numpy as np
from fastdtw import fastdtw # pip3 install fastdtw
from distance_metrics import lcs # pip3 install distance-metrics

class DistanceFuncs:
    def getNumOfMeasures(self):
        return 3

    def measure_by_index(self,index,x,y):
        x = np.hstack(x.T)
        y = np.hstack(y.T)

        if index == 0:
            return self.cos_sim(x,y)
        elif index == 1:
            return self.euclideanDistance(x,y)
        elif index == 2:
            return self.LCS(x,y)
        elif index == 3:
            return self.e_erp(x,y)
        elif index == 4:
            return self.DTW(x,y)
        return 0

    def euclideanDistance(self, x1,x2):
        return np.linalg.norm(x1 - x2)

    def DTW(self,x,y):
        distance, _ = fastdtw(x,y)
        return distance

    def LCS(self,x,y):
        return -lcs.llcs(x,y)

    def e_erp(self, t0,t1,g=0):
        """
        Usage
        -----
        The Edit distance with Real Penalty between trajectory t0 and t1.
        Parameters
        ----------
        param t0 : len(t0)x2 numpy_array
        param t1 : len(t1)x2 numpy_array
        Returns
        -------
        dtw : float
            The Dynamic-Time Warping distance between trajectory t0 and t1
        """

        n0 = len(t0)
        n1 = len(t1)
        C=np.zeros((n0+1,n1+1))

        C[1:,0]=sum(map(lambda x : abs(self.euclideanDistance(g,x)),t0))
        C[0,1:]=sum(map(lambda y : abs(self.euclideanDistance(g,y)),t1))
        for i in np.arange(n0)+1:
            for j in np.arange(n1)+1:
                derp0 = C[i-1,j] + self.euclideanDistance(t0[i-1],g)
                derp1 = C[i,j-1] + self.euclideanDistance(g,t1[j-1])
                derp01 = C[i-1,j-1] + self.euclideanDistance(t0[i-1],t1[j-1])
                C[i,j] = min(derp0,derp1,derp01)
        erp = C[n0,n1]
        return erp

    def cos_sim(self,vector_a, vector_b):
        """
        计算两个向量之间的余弦相似度
        :param vector_a: 向量 a
        :param vector_b: 向量 b
        :return: sim
        """
        if np.size(vector_a) != np.size(vector_b):
            return 0
        vector_a = np.hstack(vector_a)
        vector_b = np.hstack(vector_b)
        vector_a = np.mat(vector_a)
        vector_b = np.mat(vector_b)
        num = float(vector_a * vector_b.T)
        denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
        cos = num / denom
        sim = 0.5 + 0.5 * cos
        return -sim

disFuncs = DistanceFuncs()

if __name__ == "__main__":
    dis = DistanceFuncs()
    s1 = np.array([[0, 0, 1, 2, 1, 0, 1, 89, 0],[0, 0, 1, 2, 1, 0, 1, 9, 0],[0, 0, 1, 2, 1, 0, 1, 8, 0]])
    s2 = np.array([[0, 1, 2, 0, 0, 0, 0, 0, 0],[0, 1, 2, 0, 0, 0, 0, 0, 0],[0, 1, 2, 0, 0, 0, 0, 0, 0]])
    s2 = np.array([[0, 0, 1, 2, 1, 0, 1, 89, 0],[0, 0, 1, 2, 1, 0, 1, 9, 0],[0, 0, 1, 2, 1, 0, 1, 8, 0]])
    s1 = np.hstack(s1.T)
    s2 = np.hstack(s2.T)
    a = dis.euclideanDistance(s1, s2)
    print(a)
    pass