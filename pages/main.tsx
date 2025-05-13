import axios from 'axios';
import React, { ChangeEvent, useEffect, useState } from 'react';

const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [users, setUsers] = useState<string>('');
  const [limit, setLimit] = useState<string>('');
  const [currentUsers, setCurrentUsers] = useState<string[]>([]);
  const [currentLimit, setCurrentLimit] = useState<string>('');
  const [instagram2FA, setInstagram2FA] = useState<string>('');
  const [outsiders, setOutsiders] = useState<string>('');

  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/py/role');
        setCurrentUsers(response.data.users);
        setUsers(response.data.users.join(', '));
        setCurrentLimit(response.data.limit_by_weeks)
        setLimit(response.data.limit_by_weeks)
      } catch (error) {
        console.error('현재 Roles 불러오기 실패:', error);
      }
    };

    fetchRoles();
  }, []);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:8000/api/py/files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      alert(`파일이 성공적으로 업로드되었습니다:`);

      setOutsiders(response.data.outsiders);
      
    } catch (error) {
      console.error('파일 업로드 실패:', error);
    }
  };

  const handleUsersChange = (event: ChangeEvent<HTMLInputElement>) => {
    setUsers(event.target.value);
  };

  const handleLimitChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLimit(event.target.value);
  };

  const handleInstagram2FAChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInstagram2FA(event.target.value);
  };

  const handleUsersSubmit = async () => {
    try {
      const usersArray = users.split(',').map((user) => user.trim());

      const response = await axios.post('http://localhost:8000/api/py/users', usersArray, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      setCurrentUsers(response.data.users);
      alert(`Users 업데이트: ${response.data.users.join(', ')}`);
    } catch (error) {
      console.error('Users 업데이트 실패:', error);
    }
  };

  const handleLimitSubmit = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/py/limit_by_weeks', {
        limit: limit
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      setCurrentLimit(response.data.limit_by_weeks);
      alert(`주당 제한 수 업데이트: ${response.data.limit_by_weeks}`);
    } catch (error) {
      console.error('limit_by_weeks 업데이트 실패:', error);
    }
  };

  const handleInstaLoginSubmit = async () => {
    try {
      await axios.post('http://localhost:8000/api/py/login/instagram', {
        verification_code: instagram2FA,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      alert(`로그인 성공`);
    } catch (error) {
      alert(`로그인 실패`);
      console.error('인스타 로그인 실패:', error);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>사전 준비</h1>
      <h2>인스타그램 로그인</h2>
      <div style={{ marginTop: '20px' }}>
        <label>
        인스타그램 인증 코드:
          <input
            type="text"
            value={instagram2FA}
            onChange={handleInstagram2FAChange}
            style={{ marginLeft: '10px' }}
          />
        </label>
        <button onClick={handleInstaLoginSubmit}>인스타그램 로그인 적용하기</button>
      </div>

      <h1>카카오톡 오픈채팅방 대화내용 내보내기 파일 업로드</h1>
      
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleFileUpload}>업로드</button>

      {outsiders && (
        <div>
          <h2>🚨 삐용삐용 🚨</h2>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{outsiders}</pre>
        </div>
      )}

      <h1>주당 최대 개수:</h1>
      <div style={{ marginTop: '20px' }}>
        <label>
        주당 최대 개수:
          <input
            type="number"
            value={limit}
            onChange={handleLimitChange}
            style={{ marginLeft: '10px' }}
          />
        </label>
        <button onClick={handleLimitSubmit}>주당 최대 개수 변경하기</button>
      </div>
      <div style={{ marginTop: '20px' }}>
        <h3>현재 제한 수: {currentLimit}</h3>
      </div>

      <h1>품앗이 참여자 목록</h1>
      <div style={{ marginTop: '20px' }}>
        <label>
          참여자 입력:
          <input
            type="text"
            value={users}
            onChange={handleUsersChange}
            style={{ marginLeft: '10px' }}
          />
        </label>
        <button onClick={handleUsersSubmit}>참여자 변경하기</button>
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>현재 참여자: {currentUsers.join(', ')}</h3>
      </div>
    </div>
  );
};

export default UploadPage;