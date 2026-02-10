"""
Conversor de Postman Collection para OpenAPI 3.0
Resolve problemas de compatibilidade com exports do Postman
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs


class PostmanToOpenAPIConverter:
    """Converte Postman Collections para formato OpenAPI 3.0"""
    
    def __init__(self):
        self.openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "API Documentation",
                "version": "1.0.0",
                "description": "Generated from Postman Collection"
            },
            "servers": [],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        self.servers_set = set()
    
    def is_postman_collection(self, file_path: str) -> bool:
        """Verifica se o arquivo é uma Postman Collection"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificar indicadores de Postman Collection
            indicators = [
                'info' in data and 'schema' in data.get('info', {}),
                'item' in data,
                data.get('info', {}).get('schema', '').startswith('https://schema.getpostman.com')
            ]
            
            return any(indicators)
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            return False
    
    def convert(self, postman_file: str, output_file: str) -> bool:
        """Converte Postman Collection para OpenAPI"""
        try:
            with open(postman_file, 'r', encoding='utf-8') as f:
                postman_data = json.load(f)
            
            # Extrair informações básicas
            self._extract_info(postman_data)
            
            # Processar items (endpoints)
            if 'item' in postman_data:
                self._process_items(postman_data['item'])
            
            # Adicionar servers descobertos
            self._finalize_servers()
            
            # Salvar OpenAPI
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.openapi_spec, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erro na conversao: {e}")
            return False
    
    def _extract_info(self, postman_data: Dict[str, Any]):
        """Extrai informações básicas da collection"""
        info = postman_data.get('info', {})
        
        if 'name' in info:
            self.openapi_spec['info']['title'] = info['name']
        
        if 'description' in info:
            self.openapi_spec['info']['description'] = info['description']
        
        # Tentar extrair versão
        if 'version' in info:
            version = info['version']
            if isinstance(version, dict) and 'major' in version:
                version_str = f"{version.get('major', 1)}.{version.get('minor', 0)}.{version.get('patch', 0)}"
                self.openapi_spec['info']['version'] = version_str
    
    def _process_items(self, items: List[Dict[str, Any]], base_path: str = ""):
        """Processa items da collection (pode ser recursivo para folders)"""
        for item in items:
            if 'item' in item:
                # É uma pasta, processar recursivamente
                folder_name = item.get('name', 'folder')
                new_base_path = f"{base_path}/{self._sanitize_path(folder_name)}"
                self._process_items(item['item'], new_base_path)
            elif 'request' in item:
                # É um endpoint
                self._process_request(item, base_path)
    
    def _process_request(self, item: Dict[str, Any], base_path: str):
        """Processa um request individual"""
        request = item['request']
        
        # Extrair método HTTP
        method = request.get('method', 'GET').lower()
        
        # Extrair URL e path
        url_info = self._parse_url(request.get('url', {}))
        if not url_info:
            return
        
        # Processar path parameters
        path = self._process_path_parameters(url_info['path'])
        
        # Combinar com base_path se necessário
        if base_path and not path.startswith(base_path):
            path = f"{base_path}{path}"
        
        if not path.startswith('/'):
            path = '/' + path
        
        # Adicionar server se não existir
        if url_info['base_url']:
            self.servers_set.add(url_info['base_url'])
        
        # Criar path no OpenAPI
        if path not in self.openapi_spec['paths']:
            self.openapi_spec['paths'][path] = {}
        
        # Criar operation
        operation = {
            "summary": item.get('name', f"{method.upper()} {path}"),
            "description": item.get('description', ''),
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
        }
        
        # Processar parâmetros de query
        if url_info['query_params']:
            for param_name, param_value in url_info['query_params'].items():
                operation['parameters'].append({
                    "name": param_name,
                    "in": "query",
                    "schema": {"type": "string"},
                    "example": param_value[0] if param_value else ""
                })
        
        # Processar path parameters
        path_params = self._extract_path_parameters(path)
        for param in path_params:
            operation['parameters'].append({
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"Path parameter {param}"
            })
        
        # Processar headers
        headers = request.get('header', [])
        for header in headers:
            if isinstance(header, dict) and header.get('key'):
                # Pular headers padrão
                if header['key'].lower() not in ['content-type', 'authorization']:
                    operation['parameters'].append({
                        "name": header['key'],
                        "in": "header",
                        "schema": {"type": "string"},
                        "example": header.get('value', '')
                    })
        
        # Processar body (para POST, PUT, PATCH)
        if method in ['post', 'put', 'patch'] and 'body' in request:
            self._process_request_body(request['body'], operation)
        
        # Processar responses de exemplo
        if 'response' in item:
            self._process_responses(item['response'], operation)
        
        # Adicionar operation ao path
        self.openapi_spec['paths'][path][method] = operation
    
    def _parse_url(self, url_data) -> Optional[Dict[str, Any]]:
        """Extrai informações da URL"""
        try:
            if isinstance(url_data, str):
                url = url_data
            elif isinstance(url_data, dict):
                if 'raw' in url_data:
                    url = url_data['raw']
                elif 'host' in url_data and 'path' in url_data:
                    # Construir URL a partir de componentes
                    host = url_data['host']
                    if isinstance(host, list):
                        host = '.'.join(host)
                    
                    path = url_data['path']
                    if isinstance(path, list):
                        path = '/' + '/'.join(str(p) for p in path)
                    elif isinstance(path, str):
                        if not path.startswith('/'):
                            path = '/' + path
                    
                    protocol = url_data.get('protocol', 'https')
                    port = url_data.get('port', '')
                    port_str = f":{port}" if port else ""
                    
                    url = f"{protocol}://{host}{port_str}{path}"
                else:
                    return None
            else:
                return None
            
            # Parse da URL
            parsed = urlparse(url)
            
            # Extrair base URL
            base_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
            
            # Extrair path
            path = parsed.path or "/"
            
            # Extrair query parameters
            query_params = parse_qs(parsed.query) if parsed.query else {}
            
            return {
                'base_url': base_url,
                'path': path,
                'query_params': query_params
            }
            
        except Exception:
            return None
    
    def _process_request_body(self, body_data: Dict[str, Any], operation: Dict[str, Any]):
        """Processa o body da requisição"""
        try:
            mode = body_data.get('mode', 'raw')
            
            if mode == 'raw':
                raw_data = body_data.get('raw', '')
                content_type = "application/json"
                
                # Tentar detectar tipo de conteúdo
                options = body_data.get('options', {})
                if 'raw' in options and 'language' in options['raw']:
                    lang = options['raw']['language']
                    if lang == 'json':
                        content_type = "application/json"
                    elif lang == 'xml':
                        content_type = "application/xml"
                
                # Criar requestBody
                operation['requestBody'] = {
                    "content": {
                        content_type: {
                            "schema": {"type": "object"},
                            "example": self._parse_example_body(raw_data, content_type)
                        }
                    }
                }
            
            elif mode == 'formdata':
                # Form data
                operation['requestBody'] = {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    }
                }
                
                formdata = body_data.get('formdata', [])
                for field in formdata:
                    if isinstance(field, dict) and 'key' in field:
                        field_type = "string"
                        if field.get('type') == 'file':
                            field_type = "string"
                            operation['requestBody']['content']['multipart/form-data']['schema']['properties'][field['key']] = {
                                "type": field_type,
                                "format": "binary"
                            }
                        else:
                            operation['requestBody']['content']['multipart/form-data']['schema']['properties'][field['key']] = {
                                "type": field_type,
                                "example": field.get('value', '')
                            }
            
        except Exception as e:
            print(f"Erro ao processar body: {e}")
    
    def _parse_example_body(self, raw_data: str, content_type: str) -> Any:
        """Tenta fazer parse do exemplo de body"""
        try:
            if content_type == "application/json" and raw_data.strip():
                return json.loads(raw_data)
            else:
                return raw_data
        except json.JSONDecodeError:
            return raw_data
    
    def _process_responses(self, responses: List[Dict[str, Any]], operation: Dict[str, Any]):
        """Processa responses de exemplo"""
        try:
            for response in responses:
                if not isinstance(response, dict):
                    continue
                
                # Extrair código de status
                code = response.get('code', 200)
                if isinstance(code, str):
                    try:
                        code = int(code)
                    except ValueError:
                        code = 200
                
                # Extrair body da response
                body = response.get('body', '')
                
                # Criar response no OpenAPI
                response_obj = {
                    "description": response.get('name', f"Response {code}"),
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
                
                # Adicionar exemplo se houver body
                if body:
                    try:
                        example = json.loads(body)
                        response_obj['content']['application/json']['example'] = example
                    except json.JSONDecodeError:
                        response_obj['content']['text/plain'] = {
                            "schema": {"type": "string"},
                            "example": body
                        }
                
                operation['responses'][str(code)] = response_obj
                
        except Exception as e:
            print(f"Erro ao processar responses: {e}")
    
    def _process_path_parameters(self, path: str) -> str:
        """Converte parâmetros do Postman {{param}} para OpenAPI {param}"""
        # Converter {{param}} para {param}
        import re
        return re.sub(r'\{\{([^}]+)\}\}', r'{\1}', path)
    
    def _extract_path_parameters(self, path: str) -> List[str]:
        """Extrai nomes dos parâmetros do path"""
        import re
        matches = re.findall(r'\{([^}]+)\}', path)
        return matches
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitiza um path para uso em OpenAPI"""
        # Remover caracteres especiais e espaços
        sanitized = re.sub(r'[^\w\-_]', '_', path)
        # Remover underscores múltiplos
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remover underscores no início e fim
        sanitized = sanitized.strip('_')
        return sanitized.lower()
    
    def _finalize_servers(self):
        """Finaliza a lista de servers"""
        for server_url in self.servers_set:
            self.openapi_spec['servers'].append({
                "url": server_url,
                "description": f"Server at {server_url}"
            })
        
        # Se não há servers, adicionar um padrão
        if not self.openapi_spec['servers']:
            self.openapi_spec['servers'].append({
                "url": "https://api.example.com",
                "description": "Default server"
            })


def convert_postman_to_openapi(input_file: str, output_file: str) -> bool:
    """Função utilitária para conversão"""
    converter = PostmanToOpenAPIConverter()
    
    if not converter.is_postman_collection(input_file):
        return False
    
    return converter.convert(input_file, output_file)


# Teste da conversão
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Uso: python postman_converter.py <input.json> <output.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if convert_postman_to_openapi(input_file, output_file):
        print(f"Conversao concluida: {output_file}")
    else:
        print("Falha na conversao")