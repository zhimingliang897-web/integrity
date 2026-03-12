import paramiko
import os
import time

# SSH 配置
HOST = '8.138.164.133'
USER = 'root'
PASSWORD = '15232735822Aa'
PORT = 22

LOCAL_BASE = 'E:/integrity/docs/server'
REMOTE_BASE = '/root/integrity-api/server'

def deploy():
    print("=== Starting Deployment ===")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD)
        print("OK - Connected")
        
        sftp = ssh.open_sftp()
        
        # 需要上传的新文件
        files_to_upload = [
            ('app/main.py', 'app/main.py'),
            ('app/tools/ai_compare.py', 'app/tools/ai_compare.py'),
            ('app/tools/ai_debate.py', 'app/tools/ai_debate.py'),
            ('app/tools/dialogue_learning.py', 'app/tools/dialogue_learning.py'),
            ('app/tools/image_prompt.py', 'app/tools/image_prompt.py'),
            ('app/tools/video_maker.py', 'app/tools/video_maker.py'),
            ('requirements.txt', 'requirements.txt'),
        ]
        
        print("\nUploading files...")
        for local_rel, remote_rel in files_to_upload:
            local_path = os.path.join(LOCAL_BASE, local_rel.replace('/', os.sep))
            remote_path = f"{REMOTE_BASE}/{remote_rel}"
            
            try:
                # 确保远程目录存在
                remote_dir = os.path.dirname(remote_path)
                try:
                    sftp.stat(remote_dir)
                except:
                    ssh.exec_command(f'mkdir -p {remote_dir}')
                
                # 上传文件
                sftp.put(local_path, remote_path)
                print(f"  OK - {remote_rel}")
            except Exception as e:
                print(f"  FAIL - {remote_rel}: {e}")
        
        sftp.close()
        
        # 安装依赖
        print("\nInstalling dependencies...")
        stdin, stdout, stderr = ssh.exec_command(f'cd {REMOTE_BASE} && pip install -r requirements.txt -q')
        stdout.read()
        
        # 重启服务
        print("Restarting service...")
        ssh.exec_command('pkill gunicorn || true')
        time.sleep(1)
        
        start_cmd = f'''cd {REMOTE_BASE} && gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon \\
          --error-logfile {REMOTE_BASE}/gunicorn.error.log \\
          --access-logfile {REMOTE_BASE}/gunicorn.access.log \\
          --env SECRET_KEY=integrity-lab-secret-2026 \\
          --env DASHSCOPE_API_KEY=sk-0ef56d1b3ba54a188ce28a46c54e2a24 \\
          --env INVITE_CODES=demo2026,friend2026,test2026'''
        
        ssh.exec_command(start_cmd)
        time.sleep(3)
        
        # 验证
        print("\nVerifying...")
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/')
        result = stdout.read().decode('utf-8')
        print(f"Response: {result}")
        
        # 检查新端点
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/api/tools/ai-compare/providers')
        result = stdout.read().decode('utf-8')
        print(f"AI Compare: {result[:200]}...")
        
        print("\n=== Deployment Completed ===")
        
    except Exception as e:
        print(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    deploy()