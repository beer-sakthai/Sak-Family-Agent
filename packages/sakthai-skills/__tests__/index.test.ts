import http from 'http';
import { server } from '../src/index';

describe('HTTP Server Router', () => {
  let activeServer: http.Server;
  let port: number;

  beforeAll((done) => {
    activeServer = server.listen(0, '127.0.0.1', () => {
      const address = activeServer.address() as any;
      port = address.port;
      done();
    });
  });

  afterAll((done) => {
    activeServer.close(done);
  });

  test('GET /health should return 200 and status ok', (done) => {
    http.get(`http://127.0.0.1:${port}/health`, (res) => {
      expect(res.statusCode).toBe(200);
      expect(res.headers['content-type']).toBe('application/json');

      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        const payload = JSON.parse(body);
        expect(payload).toEqual({ status: 'ok', service: 'sakthai-skills' });
        done();
      });
    });
  });

  test('GET unknown URL should return 404', (done) => {
    http.get(`http://127.0.0.1:${port}/unknown-path`, (res) => {
      expect(res.statusCode).toBe(404);
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        const payload = JSON.parse(body);
        expect(payload).toEqual({ error: 'Not Found' });
        done();
      });
    });
  });
});
